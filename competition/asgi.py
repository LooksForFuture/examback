"""
ASGI config for competition project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

import app_test.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'competition.settings')

print("La Li Lu Le Lo")

#application = get_asgi_application()
application = ProtocolTypeRouter({
    'http':get_asgi_application(),
    'websocket':AuthMiddlewareStack(
        URLRouter(
            app_test.routing.websocket_urlpatterns
        )
    )
})