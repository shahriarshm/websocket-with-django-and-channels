from channels.generic.websocket import WebsocketConsumer
from channels.exceptions import StopConsumer
from asgiref.sync import async_to_sync
import json

class EchoConsumer(WebsocketConsumer):
    def connect(self):

        self.accept()
        
    def disconnect(self, close_code):
        pass

    def receive(self, text_data=None, bytes_data=None):
        self.send(text_data=text_data + " - Sent By Server")
        
