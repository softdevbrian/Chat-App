import json
from django.test import TestCase
from channels.testing import WebsocketCommunicator
from chat_project.asgi import application

class ChatConsumerTests(TestCase):
    """
    Automated test suite verifying the WebSocket echo consumer lifecycle.
    """

    async def test_echo_consumer(self):
        # 1. Connect to WebSocket route
        communicator = WebsocketCommunicator(application, "/ws/chat/test/")
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected, "WebSocket connection was rejected.")

        # 2. Check initial welcome response
        welcome_response = await communicator.receive_json_from()
        self.assertEqual(welcome_response["type"], "connection_established")
        self.assertIn("Connected", welcome_response["message"])

        # 3. Send message payload
        await communicator.send_json_to({"message": "Hello Channels!"})

        # 4. Verify echo response
        echo_response = await communicator.receive_json_from()
        self.assertEqual(echo_response["type"], "echo_response")
        self.assertEqual(echo_response["message"], "Echo from server: Hello Channels!")

        # 5. Disconnect cleanly
        await communicator.disconnect()
