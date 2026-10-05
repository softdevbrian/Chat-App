from django.urls import re_path
from . import consumers

# Dynamic WebSocket routing matching room names (e.g. ws/chat/lounge/, ws/chat/room1/)
websocket_urlpatterns = [
    re_path(r'^ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
]
