from django.urls import path

from echo import consumers

websocket_urlpatterns = [
    path('ws/', consumers.EchoConsumer.as_asgi()),
    path('ws/chat/<str:username>/', consumers.ChatConsumer.as_asgi()),
    path('ws/chat2/<str:username>/', consumers.ChatConsumer2.as_asgi())
]