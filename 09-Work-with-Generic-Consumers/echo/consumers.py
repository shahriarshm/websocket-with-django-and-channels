from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer, JsonWebsocketConsumer, AsyncJsonWebsocketConsumer
from channels.exceptions import StopConsumer
from asgiref.sync import async_to_sync
import json

class EchoConsumer(WebsocketConsumer):
    def connect(self):

        self.accept()
        
    def disconnect(self, close_code):
        pass

    def receive(self, text_data=None, bytes_data=None):
        if text_data:
            self.send(text_data=text_data + " - Sent By Server")
        elif bytes_data:
            self.send(bytes_data=bytes_data)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['username']
        self.group_name = f"chat_{self.user_id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            text_data_json = json.loads(text_data)
            username = text_data_json['receiver']
            user_group_name = f"chat_{username}"
            
            await self.channel_layer.group_send(
                user_group_name,
                {
                    'type': 'chat_message',
                    'message': text_data
                }
            )

    async def chat_message(self, event):
        message = event['message']

        await self.send(text_data=message)


class TestConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
    
        await self.accept()
    
    async def disconnect(self, close_code):
        pass

    async def receive_json(self, content):
        await self.send_json(content)
        


