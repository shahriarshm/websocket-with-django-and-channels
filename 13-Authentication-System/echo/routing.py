from django.urls import path

from echo import consumers

websocket_urlpatterns = [
    path('ws/', consumers.EchoConsumer),
    path('ws/echo/chat/<str:username>/', consumers.ChatConsumer),
    path('ws/echo/chat/<str:username>/', consumers.ChatConsumer2)
]