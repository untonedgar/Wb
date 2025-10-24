"""
ASGI config for app project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStac
from chat import websoket_urls
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

django_asgi_app = get_asgi_application()





application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websoket_urls.websocket_urlpatterns
        )
    ),
})
