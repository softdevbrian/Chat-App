import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Conversation, Message, UserProfile


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Real-time WebSocket consumer supporting:
    1. Persistent database message storage (SQLite)
    2. Automatic 100-message FIFO pruning
    3. User presence rosters per conversation
    4. Group deletion broadcasting
    """

    # Class-level presence tracker: { group_channel_name: { channel_name: username } }
    rosters = {}

    async def connect(self):
        url_kwargs = self.scope['url_route']['kwargs']

        if 'conversation_id' in url_kwargs:
            self.conversation_id = url_kwargs['conversation_id']
            self.room_group_name = f'conv_{self.conversation_id}'
        else:
            self.room_name = url_kwargs.get('room_name', 'general')
            self.room_group_name = f'chat_{self.room_name}'
            self.conversation_id = None

        self.user = self.scope.get('user', None)
        self.username = self.user.username if (self.user and self.user.is_authenticated) else None

        # Subscribe to Channel Layer group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # If user is authenticated, register presence right away
        if self.username:
            await self.register_user_presence(self.username)

    async def disconnect(self, close_code):
        # Discard from Channel Layer group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # Remove from active presence roster
        if self.room_group_name in ChatConsumer.rosters:
            roster = ChatConsumer.rosters[self.room_group_name]
            departed_user = roster.pop(self.channel_name, self.username)

            if not roster:
                ChatConsumer.rosters.pop(self.room_group_name, None)
                distinct_users = []
            else:
                distinct_users = sorted(list(set(roster.values())))

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
        try:
            data = json.loads(text_data)
        except (json.JSONDecodeError, TypeError):
            return

        msg_type = data.get('type')

        if msg_type == 'set_username':
            raw_username = data.get('username', '').strip()
            if raw_username:
                self.username = raw_username
                await self.register_user_presence(self.username)

        elif msg_type == 'chat_message':
            text = data.get('message', '').strip()
            sender_name = self.username or data.get('sender', 'Anonymous')
            if not text:
                return

            avatar_id = 'avatar_1'
            saved_msg_data = None

            # Persist to SQLite database asynchronously
            if self.conversation_id and self.user and self.user.is_authenticated:
                saved_msg_data = await self.save_message_to_db(self.conversation_id, self.user, text)
                avatar_id = saved_msg_data.get('avatar_id', 'avatar_1')
                timestamp = saved_msg_data.get('timestamp', '')
            else:
                from datetime import datetime
                timestamp = datetime.now().strftime("%I:%M %p")

            # Broadcast message to all participants in this conversation
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_chat_message',
                    'message': text,
                    'sender': sender_name,
                    'avatar_id': avatar_id,
                    'timestamp': timestamp
                }
            )

    async def register_user_presence(self, username):
        if self.room_group_name not in ChatConsumer.rosters:
            ChatConsumer.rosters[self.room_group_name] = {}
        ChatConsumer.rosters[self.room_group_name][self.channel_name] = username

        distinct_users = sorted(list(set(ChatConsumer.rosters[self.room_group_name].values())))

        # Send current user roster to the connecting client
        await self.send(text_data=json.dumps({
            'type': 'user_list',
            'users': distinct_users
        }))

        # Broadcast join notification
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'username': username,
                'users': distinct_users
            }
        )

    # --------------------------------------------------------------------------
    # CHANNEL LAYER HANDLERS
    # --------------------------------------------------------------------------

    async def broadcast_chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender': event['sender'],
            'avatar_id': event.get('avatar_id', 'avatar_1'),
            'timestamp': event.get('timestamp', '')
        }))

    async def user_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'username': event['username'],
            'users': event['users']
        }))

    async def user_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'username': event['username'],
            'users': event['users']
        }))

    async def group_deleted(self, event):
        """Notifies clients that this group has been deleted by its owner."""
        await self.send(text_data=json.dumps({
            'type': 'group_deleted',
            'group_id': event['group_id'],
            'group_name': event['group_name'],
            'deleted_by': event['deleted_by']
        }))

    # --------------------------------------------------------------------------
    # DATABASE ASYNC WRAPPERS
    # --------------------------------------------------------------------------

    @database_sync_to_async
    def save_message_to_db(self, conv_id, user, text):
        try:
            conv = Conversation.objects.get(id=conv_id)
            msg = Message.objects.create(
                conversation=conv,
                sender=user,
                text=text
            )
            profile = getattr(user, 'profile', None)
            avatar_id = profile.avatar_id if profile else 'avatar_1'
            return {
                'id': msg.id,
                'avatar_id': avatar_id,
                'timestamp': msg.timestamp.strftime("%I:%M %p")
            }
        except Exception as e:
            print("Error persisting message:", e)
            from datetime import datetime
            return {
                'id': 0,
                'avatar_id': 'avatar_1',
                'timestamp': datetime.now().strftime("%I:%M %p")
            }
