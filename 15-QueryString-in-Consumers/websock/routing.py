from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.sessions import SessionMiddlewareStack

from echo import routing as echo_routing

application = ProtocolTypeRouter({
    'websocket': SessionMiddlewareStack(
        AuthMiddlewareStack(
            URLRouter(
                echo_routing.websocket_urlpatterns
            )
        )
    )
})
