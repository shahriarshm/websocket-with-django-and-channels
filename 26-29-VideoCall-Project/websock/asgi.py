import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from channels.sessions import SessionMiddlewareStack
from channels.security.websocket import OriginValidator, AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'websock.settings')

django_asgi_app = get_asgi_application()

from echo import routing as echo_routing
from chat import routing as chat_routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        SessionMiddlewareStack(
            AuthMiddlewareStack(
                URLRouter(
                    echo_routing.websocket_urlpatterns +
                    chat_routing.websocket_urlpatterns
                )
            )
        )
    )
})
