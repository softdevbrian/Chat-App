import json
from django.test import TestCase, Client
from django.urls import reverse
from channels.testing import WebsocketCommunicator
from chat_project.asgi import application
from chat.consumers import ChatConsumer

class ChatViewTests(TestCase):
    """
    Automated test suite verifying the HTTP frontend views and templates.
    """

    def setUp(self):
        self.client = Client()

    def test_lobby_view(self):
        response = self.client.get(reverse('chat:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat/index.html')
        self.assertContains(response, 'Tuko Chat')

    def test_room_view(self):
        response = self.client.get(reverse('chat:room', args=['lounge']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat/room.html')
        self.assertContains(response, 'lounge')


class UserPresenceAndBroadcastingTests(TestCase):
    """
    Automated test suite verifying user presence tracking, join/leave
    notifications, online user lists, and room isolation.
    """

    def setUp(self):
        # Reset class-level roster before each test
        ChatConsumer.room_rosters.clear()

    def tearDown(self):
        ChatConsumer.room_rosters.clear()

    async def test_user_presence_lifecycle(self):
        # 1. Alice connects to room 'lobby'
        alice = WebsocketCommunicator(application, "/ws/chat/lobby/")
        connected_a, _ = await alice.connect()
        self.assertTrue(connected_a)

        # 2. Alice sends set_username handshake
        await alice.send_json_to({
            "type": "set_username",
            "username": "Alice"
        })

        # Alice receives initial user_list
        list_msg = await alice.receive_json_from()
        self.assertEqual(list_msg["type"], "user_list")
        self.assertEqual(list_msg["users"], ["Alice"])

        # Alice receives user_joined announcement
        join_msg = await alice.receive_json_from()
        self.assertEqual(join_msg["type"], "user_joined")
        self.assertEqual(join_msg["username"], "Alice")

        # 3. Bob connects to the same room 'lobby'
        bob = WebsocketCommunicator(application, "/ws/chat/lobby/")
        connected_b, _ = await bob.connect()
        self.assertTrue(connected_b)

        await bob.send_json_to({
            "type": "set_username",
            "username": "Bob"
        })

        # Bob receives initial user_list with both users
        bob_list = await bob.receive_json_from()
        self.assertEqual(bob_list["type"], "user_list")
        self.assertEqual(sorted(bob_list["users"]), ["Alice", "Bob"])

        # Both Alice and Bob receive user_joined for Bob
        bob_join_for_alice = await alice.receive_json_from()
        self.assertEqual(bob_join_for_alice["type"], "user_joined")
        self.assertEqual(bob_join_for_alice["username"], "Bob")
        self.assertEqual(sorted(bob_join_for_alice["users"]), ["Alice", "Bob"])

        bob_join_for_bob = await bob.receive_json_from()
        self.assertEqual(bob_join_for_bob["type"], "user_joined")
        self.assertEqual(bob_join_for_bob["username"], "Bob")

        # 4. Charlie connects to a DIFFERENT room 'gaming' (Isolation check)
        charlie = WebsocketCommunicator(application, "/ws/chat/gaming/")
        connected_c, _ = await charlie.connect()
        self.assertTrue(connected_c)

        await charlie.send_json_to({
            "type": "set_username",
            "username": "Charlie"
        })
        charlie_list = await charlie.receive_json_from()
        self.assertEqual(charlie_list["users"], ["Charlie"])
        await charlie.receive_json_from() # charlie join announcement

        # 5. Alice sends a chat message
        await alice.send_json_to({
            "type": "chat_message",
            "message": "Hello Bob!"
        })

        chat_alice = await alice.receive_json_from()
        self.assertEqual(chat_alice["type"], "chat_message")
        self.assertEqual(chat_alice["message"], "Hello Bob!")
        self.assertEqual(chat_alice["sender"], "Alice")

        chat_bob = await bob.receive_json_from()
        self.assertEqual(chat_bob["type"], "chat_message")
        self.assertEqual(chat_bob["message"], "Hello Bob!")

        # Charlie in gaming receives nothing from lobby
        self.assertTrue(await charlie.receive_nothing(timeout=0.1))

        # 6. Bob disconnects -> Alice must receive user_left for Bob
        await bob.disconnect()

        leave_msg = await alice.receive_json_from()
        self.assertEqual(leave_msg["type"], "user_left")
        self.assertEqual(leave_msg["username"], "Bob")
        self.assertEqual(leave_msg["users"], ["Alice"])

        # 7. Clean up remaining
        await alice.disconnect()
        await charlie.disconnect()
