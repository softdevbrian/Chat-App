import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    """
    Multi-room broadcasting consumer for Django Channels.
    Manages group membership (join, broadcast, leave) using the Channel Layer.
    """

    async def connect(self):
        """
        Called when a WebSocket connection is initiated.
        Extracts room name from URL, adds channel to group, and accepts handshake.
        """
        # Extract room_name from the URL route parameters (scope['url_route']['kwargs'])
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # Add this individual connection channel to the named room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Accept the WebSocket handshake
        await self.accept()

        # Send connection confirmation to THIS connecting client
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'room': self.room_name,
            'message': f'Connected to room: {self.room_name}'
        }))

    async def disconnect(self, close_code):
        """
        Called when the WebSocket connection terminates.
        Removes this connection channel from the room group.
        """
        # Remove this channel from the room group to avoid dead broadcasting
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        """
        Called when a client sends a message down its WebSocket.
        Broadcasts the message to all channels in the room group.
        """
        # Parse payload with safe error handling
        try:
            data = json.loads(text_data)
            message = data.get('message', '')
            sender = data.get('sender', 'Anonymous')
        except (json.JSONDecodeError, TypeError):
            message = text_data or ''
            sender = 'Anonymous'

        # Broadcast the message to all subscribers of the room group
        # The 'type' string ('chat_message') routes to the method chat_message below!
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender
            }
        )

    async def chat_message(self, event):
        """
        Handler invoked by Channels when a 'chat_message' event is received
        from the channel layer group. Sends the payload down THIS client's WebSocket.
        """
        message = event['message']
        sender = event.get('sender', 'Anonymous')

        # Push the message to the connected client
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message,
            'sender': sender
        }))
