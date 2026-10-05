import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    """
    Multi-room broadcasting consumer with user presence tracking.
    Maintains an active roster of users per room, announcing joins, leaves,
    and syncing online user lists.
    """

    # Class-level dictionary tracking active connections per room:
    # { room_group_name: { channel_name: username } }
    room_rosters = {}

    async def connect(self):
        """
        Called when a client initiates a WebSocket connection.
        Extracts room parameters, subscribes to room group, and accepts connection.
        """
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.username = None

        # Add this individual connection channel to the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Accept the WebSocket handshake
        await self.accept()

    async def disconnect(self, close_code):
        """
        Called when the WebSocket connection terminates.
        Removes channel from room group and updates online user presence.
        """
        # Remove channel from group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # Remove connection from room presence roster
        if self.room_group_name in ChatConsumer.room_rosters:
            roster = ChatConsumer.room_rosters[self.room_group_name]
            departed_user = roster.pop(self.channel_name, self.username)

            # Prune empty room dictionaries to prevent memory leaks
            if not roster:
                ChatConsumer.room_rosters.pop(self.room_group_name, None)
                distinct_users = []
            else:
                distinct_users = sorted(list(set(roster.values())))

            # If this user has no other open tabs in this room, broadcast user_left
            if departed_user and departed_user not in distinct_users:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'user_left',
                        'username': departed_user,
                        'users': distinct_users
                    }
                )

    async def receive(self, text_data=None, bytes_data=None):
        """
        Called when a message arrives from the client.
        Dispatches according to the 'type' field in the JSON payload.
        """
        try:
            data = json.loads(text_data)
        except (json.JSONDecodeError, TypeError):
            return

        msg_type = data.get('type')

        if msg_type == 'set_username':
            # Initial handshake registering the client's username
            raw_username = data.get('username', 'Anonymous').strip()
            self.username = raw_username if raw_username else 'Anonymous'

            # Record in class-level roster
            if self.room_group_name not in ChatConsumer.room_rosters:
                ChatConsumer.room_rosters[self.room_group_name] = {}
            ChatConsumer.room_rosters[self.room_group_name][self.channel_name] = self.username

            distinct_users = sorted(list(set(ChatConsumer.room_rosters[self.room_group_name].values())))

            # 1. Send current full user list directly to the connecting client
            await self.send(text_data=json.dumps({
                'type': 'user_list',
                'users': distinct_users
            }))

            # 2. Broadcast join event to everyone in the room (including updated user list)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_joined',
                    'username': self.username,
                    'users': distinct_users
                }
            )

        elif msg_type == 'chat_message':
            # Standard chat message broadcast
            message = data.get('message', '').strip()
            if not message:
                return

            sender = self.username or data.get('sender', 'Anonymous')

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender': sender
                }
            )

    # -------------------------------------------------------------------------
    # Channel Layer Group Event Handlers
    # -------------------------------------------------------------------------

    async def chat_message(self, event):
        """Forwards a chat message down to this client's WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender': event['sender']
        }))

    async def user_joined(self, event):
        """Notifies this client that a user has joined."""
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'username': event['username'],
            'users': event['users']
        }))

    async def user_left(self, event):
        """Notifies this client that a user has left."""
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'username': event['username'],
            'users': event['users']
        }))
