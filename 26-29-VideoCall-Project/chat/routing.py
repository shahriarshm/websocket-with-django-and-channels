from django.urls import path

from chat import consumers

websocket_urlpatterns = [
    path('ws/chat/<str:chat_id>/', consumers.ChatConsumer),
    path('ws/videochat/', consumers.VideoChatConsumer)
]