from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer, JsonWebsocketConsumer, AsyncJsonWebsocketConsumer
from channels.consumer import SyncConsumer, AsyncConsumer
from channels.exceptions import StopConsumer
from asgiref.sync import async_to_sync
import json
import urllib.parse as urlparse

class EchoConsumer(WebsocketConsumer):
    def connect(self):
        self.room_id = "echo_1"
        self.user = self.scope['user']
        username = self.user.username

        self.scope['session']['test'] = 1
        self.scope['session']['test2'] = username
        self.scope['session'].save()

        query = self.scope['query_string']
        params = urlparse.parse_qs(query.decode('UTF-8'))

        name = params.get('name', [None])[0]
        version = params.get('version', [None])[0]

        print(name, version)

        if self.user.is_staff:
            async_to_sync(self.channel_layer.group_add)(
                self.room_id,
                self.channel_name
            )
            self.accept()
        else:
            self.close()
    
    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_id,
            self.channel_name
        )

    def receive(self, text_data=None, bytes_data=None):
        if text_data:
            self.send(text_data=text_data + " - Sent By Server")
        elif bytes_data:
            self.send(bytes_data=bytes_data)

    def echo_message(self, event):
        message = event['message']

        self.send(text_data=message)


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


class ChatConsumer2(AsyncConsumer):
    async def websocket_connect(self, event):
        self.user_id = self.scope['url_route']['kwargs']['username']
        self.group_name = f"chat_{self.user_id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.send({
            'type': 'websocket.accept'
        })

    async def websocket_disconnect(self, event):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        raise StopConsumer()


    async def websocket_receive(self, event):
        text_data = event.get('text', None)
        bytes_data = event.get('bytes', None)

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
            await self.channel_layer.group_send(
                'echo_1',
                {
                    'type': 'echo_message',
                    'message': text_data
                }
            )

    async def chat_message(self, event):
        message = event['message']

        await self.send({
            'type': 'websocket.send',
            'text': message
        })



class TestConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
    
        await self.accept()
    
    async def disconnect(self, close_code):
        pass

    async def receive_json(self, content):
        await self.send_json(content)
        


