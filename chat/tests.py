import json
from django.test import TestCase
from channels.testing import WebsocketCommunicator
from chat_project.asgi import application

class RoomGroupTests(TestCase):
    """
    Automated test suite verifying multi-room isolation and group broadcasting.
    """

    async def test_room_group_broadcasting_and_isolation(self):
        # 1. Connect Alice and Bob to room 'general'
        alice = WebsocketCommunicator(application, "/ws/chat/general/")
        connected_a, _ = await alice.connect()
        self.assertTrue(connected_a)

        bob = WebsocketCommunicator(application, "/ws/chat/general/")
        connected_b, _ = await bob.connect()
        self.assertTrue(connected_b)

        # 2. Connect Charlie to a completely different room: 'gaming'
        charlie = WebsocketCommunicator(application, "/ws/chat/gaming/")
        connected_c, _ = await charlie.connect()
        self.assertTrue(connected_c)

        # 3. Consume welcome messages
        welcome_a = await alice.receive_json_from()
        self.assertEqual(welcome_a["room"], "general")

        welcome_b = await bob.receive_json_from()
        self.assertEqual(welcome_b["room"], "general")

        welcome_c = await charlie.receive_json_from()
        self.assertEqual(welcome_c["room"], "gaming")

        # 4. Alice sends a message to room 'general'
        await alice.send_json_to({
            "message": "Hey everyone in general!",
            "sender": "Alice"
        })

        # 5. Alice should receive the broadcast
        msg_alice = await alice.receive_json_from()
        self.assertEqual(msg_alice["type"], "chat_message")
        self.assertEqual(msg_alice["message"], "Hey everyone in general!")
        self.assertEqual(msg_alice["sender"], "Alice")

        # 6. Bob (in the same room) MUST also receive the broadcast
        msg_bob = await bob.receive_json_from()
        self.assertEqual(msg_bob["type"], "chat_message")
        self.assertEqual(msg_bob["message"], "Hey everyone in general!")
        self.assertEqual(msg_bob["sender"], "Alice")

        # 7. Charlie (in 'gaming' room) MUST NOT receive anything from 'general'
        no_message_for_charlie = await charlie.receive_nothing(timeout=0.1)
        self.assertTrue(no_message_for_charlie, "Charlie received a message from a room he did not join!")

        # 8. Clean disconnection
        await alice.disconnect()
        await bob.disconnect()
        await charlie.disconnect()
