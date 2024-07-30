from django.urls import path

from echo import consumers

websocket_urlpatterns = [
    path('ws/', consumers.EchoConsumer.as_asgi()),
    path('ws/echo/chat/<str:username>/', consumers.ChatConsumer.as_asgi()),
]