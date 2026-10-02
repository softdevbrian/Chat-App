from django.urls import re_path
from . import consumers

# WebSocket routing table for the chat app
websocket_urlpatterns = [
    re_path(r'^ws/chat/test/$', consumers.ChatConsumer.as_asgi()),
]
