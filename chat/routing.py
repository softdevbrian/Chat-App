from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Conversation-based routing for 1-on-1 DMs and Groups
    re_path(r'^ws/conversation/(?P<conversation_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
    # Legacy room name routing
    re_path(r'^ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
]
