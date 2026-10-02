import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    """
    Echo consumer for learning WebSockets with Django Channels.
    Receives messages from a client and immediately echoes them back.
    """

    async def connect(self):
        """
        Called when a client initiates a WebSocket connection handshake.
        Accepts the connection and sends a welcome message.
        """
        # Accept the WebSocket handshake
        await self.accept()

        # Send an initial welcome confirmation to the connecting client
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to Django Channels Echo Server!'
        }))

    async def disconnect(self, close_code):
        """
        Called when the WebSocket closes (tab closed, network dropped, etc.).
        """
        # No group cleanup needed yet for simple echo
        pass

    async def receive(self, text_data=None, bytes_data=None):
        """
        Called when the client sends a message down the WebSocket pipe.
        """
        # Parse incoming payload with safe JSON error handling
        try:
            data = json.loads(text_data)
            message = data.get('message', '')
        except (json.JSONDecodeError, TypeError):
            # Fallback in case raw unformatted text was sent
            message = text_data or ''

        # Echo the message back to the same client
        await self.send(text_data=json.dumps({
            'type': 'echo_response',
            'message': f'Echo from server: {message}'
        }))
