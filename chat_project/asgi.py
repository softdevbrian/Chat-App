"""
ASGI config for chat_project project.

Routes standard HTTP traffic to Django's ASGI application and
WebSocket connections to Django Channels URLRouter.
"""

import os
from django.core.asgi import get_asgi_application

# Ensure Django settings module is defined before initializing Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_project.settings')

# Initialize Django ASGI application early to ensure the app registry is populated
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chat.routing

# The root ASGI application router
application = ProtocolTypeRouter({
    # Standard HTTP requests
    "http": django_asgi_app,

    # WebSocket connections
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})
