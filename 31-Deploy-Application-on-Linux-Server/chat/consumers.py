from channels.consumer import SyncConsumer, AsyncConsumer
from channels.exceptions import StopConsumer
from asgiref.sync import async_to_sync
import json
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.db.models import Q
from chat.models import GroupChat, Message, VideoThread
import asyncio
from datetime import datetime

class ChatConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        self.user = self.scope['user']
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.chat = await self.get_chat()
        self.chat_room_id = f"chat_{self.chat_id}"

        if self.chat:
            await self.channel_layer.group_add(
                self.chat_room_id,
                self.channel_name
            )

            await self.send({
                'type': 'websocket.accept'
            })
        else:
            await self.send({
                'type': 'websocket.close'
            })


    async def websocket_disconnect(self, event):
        await self.channel_layer.group_discard(
            self.chat_room_id,
            self.channel_name
        )
        raise StopConsumer()


    async def websocket_receive(self, event):
        text_data = event.get('text', None)
        bytes_data = event.get('bytes', None)

        if text_data:
            text_data_json = json.loads(text_data)
            text = text_data_json['text']

            await self.create_message(text)
            
            await self.channel_layer.group_send(
                self.chat_room_id,
                {
                    'type': 'chat_message',
                    'message': json.dumps({'type':"msg", 'sender':self.user.username, 'text':text}),
                    'sender_channel_name': self.channel_name
                }
            )

    async def chat_message(self, event):
        message = event['message']
        
        if self.channel_name != event['sender_channel_name']:
            await self.send({
                'type': 'websocket.send',
                'text': message
            })

    async def chat_activity(self, event):
        message = event['message']

        await self.send({
            'type': 'websocket.send',
            'text': message
        })

    @database_sync_to_async
    def get_chat(self):
        try:
            chat = GroupChat.objects.get(unique_code=self.chat_id)
            return chat
        except GroupChat.DoesNotExist:
            return None

    @database_sync_to_async
    def create_message(self, text):
        Message.objects.create(chat_id=self.chat.id, author_id=self.user.id, text=text)

# Video Call Status
VC_CONTACTING, VC_NOT_AVAILABLE, VC_ACCEPTED, VC_REJECTED, VC_BUSY, VC_PROCESSING, VC_ENDED = \
    0, 1, 2, 3, 4, 5, 6

class VideoChatConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        self.user = self.scope['user']
        self.user_room_id = f"videochat_{self.user.id}"

        await self.channel_layer.group_add(
            self.user_room_id,
            self.channel_name
        )

        await self.send({
            'type': 'websocket.accept'
        })
      

    async def websocket_disconnect(self, event):
        video_thread_id = self.scope['session'].get('video_thread_id', None)
        videothread = await self.change_videothread_status(video_thread_id, VC_ENDED)
        if videothread is not None:
            await self.change_videothread_datetime(video_thread_id, False)
            await self.channel_layer.group_send(
                f"videochat_{videothread.caller.id}",
                {
                    'type': 'chat_message',
                    'message': json.dumps({'type': "offerResult", 'status': VC_ENDED, 'video_thread_id': videothread.id}),
                }
            )
            await self.channel_layer.group_send(
                f"videochat_{videothread.callee.id}",
                {
                    'type': 'chat_message',
                    'message': json.dumps({'type': "offerResult", 'status': VC_ENDED, 'video_thread_id': videothread.id}),
                }
            )
        await self.channel_layer.group_discard(
            self.user_room_id,
            self.channel_name
        )
        raise StopConsumer()


    async def websocket_receive(self, event):
        text_data = event.get('text', None)
        bytes_data = event.get('bytes', None)

        if text_data:
            text_data_json = json.loads(text_data)
            message_type = text_data_json['type']
            
            if message_type == "createOffer":
                callee_username = text_data_json['username']
                status, video_thread_id = await self.create_videothread(callee_username)

                await self.send({
                    'type': 'websocket.send',
                    'text': json.dumps({'type': "offerResult", 'status': status, 'video_thread_id': video_thread_id})
                })

                if status == VC_CONTACTING:
                    videothread = await self.get_videothread(video_thread_id)

                    await self.channel_layer.group_send(
                        f"videochat_{videothread.callee.id}",
                        {
                            'type': 'chat_message',
                            'message': json.dumps({'type':"offer", 'username': self.user.username, 'video_thread_id': video_thread_id}),
                        }
                    )

            elif message_type == "cancelOffer":
                video_thread_id = text_data_json['video_thread_id']
                videothread = await self.get_videothread(video_thread_id)
                self.scope['session']['video_thread_id'] = None
                self.scope['session'].save()
                
                if videothread.status != VC_ACCEPTED or videothread.status != VC_REJECTED:
                    await self.change_videothread_status(video_thread_id, VC_NOT_AVAILABLE)
                    await self.send({
                        'type': 'websocket.send',
                        'text': json.dumps({'type': "offerResult", 'status': VC_NOT_AVAILABLE, 'video_thread_id': videothread.id})
                    })
                    await self.channel_layer.group_send(
                        f"videochat_{videothread.callee.id}",
                        {
                            'type': 'chat_message',
                            'message': json.dumps({'type':"offerFinished"}),
                        }
                    )

            elif message_type == "acceptOffer":
                video_thread_id = text_data_json['video_thread_id']
                videothread = await self.change_videothread_status(video_thread_id, VC_PROCESSING)
                await self.change_videothread_datetime(video_thread_id, True)

                await self.channel_layer.group_send(
                    f"videochat_{videothread.caller.id}",
                    {
                        'type': 'chat_message',
                        'message': json.dumps({'type': "offerResult", 'status': VC_ACCEPTED, 'video_thread_id': videothread.id}),
                    }
                )

            elif message_type == "rejectOffer":
                video_thread_id = text_data_json['video_thread_id']
                videothread = await self.change_videothread_status(video_thread_id, VC_REJECTED)
                self.scope['session']['video_thread_id'] = None
                self.scope['session'].save()

                await self.channel_layer.group_send(
                    f"videochat_{videothread.caller.id}",
                    {
                        'type': 'chat_message',
                        'message': json.dumps({'type': "offerResult", 'status': VC_REJECTED, 'video_thread_id': videothread.id}),
                    }
                )

            elif message_type == "hangUp":
                video_thread_id = text_data_json['video_thread_id']
                videothread = await self.change_videothread_status(video_thread_id, VC_ENDED)
                await self.change_videothread_datetime(video_thread_id, False)
                self.scope['session']['video_thread_id'] = None
                self.scope['session'].save()

                await self.channel_layer.group_send(
                    f"videochat_{videothread.caller.id}",
                    {
                        'type': 'chat_message',
                        'message': json.dumps({'type': "offerResult", 'status': VC_ENDED, 'video_thread_id': videothread.id}),
                    }
                )
                await self.channel_layer.group_send(
                    f"videochat_{videothread.callee.id}",
                    {
                        'type': 'chat_message',
                        'message': json.dumps({'type': "offerResult", 'status': VC_ENDED, 'video_thread_id': videothread.id}),
                    }
                )
            
            elif message_type == "callerData":
                video_thread_id = text_data_json['video_thread_id']
                videothread = await self.get_videothread(video_thread_id)
            
                await self.channel_layer.group_send(
                    f"videochat_{videothread.callee.id}",
                    {
                        'type': 'chat_message',
                        'message': text_data,
                    }
                )

            elif message_type == "calleeData":
                video_thread_id = text_data_json['video_thread_id']
                videothread = await self.get_videothread(video_thread_id)

                await self.channel_layer.group_send(
                    f"videochat_{videothread.caller.id}",
                    {
                        'type': 'chat_message',
                        'message': text_data,
                    }
                )

    
    async def chat_message(self, event):
        message = event['message']

        await self.send({
            'type': 'websocket.send',
            'text': message
        })

    @database_sync_to_async
    def get_videothread(self, id):
        try:
            videothread = VideoThread.objects.get(id=id)
            return videothread
        except VideoThread.DoesNotExist:
            return None

    @database_sync_to_async
    def create_videothread(self, callee_username):
        try:
            callee = User.objects.get(username=callee_username)
        except User.DoesNotExist:
            return 404, None

        if VideoThread.objects.filter(Q(caller_id=callee.id) | Q(callee_id=callee.id), status=VC_PROCESSING).count() > 0:
            return VC_BUSY, None
        
        videothread = VideoThread.objects.create(caller_id=self.user.id, callee_id=callee.id)
        self.scope['session']['video_thread_id'] = videothread.id
        self.scope['session'].save()

        return VC_CONTACTING, videothread.id

    @database_sync_to_async
    def change_videothread_status(self, id, status):
        try:
            videothread = VideoThread.objects.get(id=id)
            videothread.status = status
            videothread.save()
            return videothread
        except VideoThread.DoesNotExist:
            return None

    @database_sync_to_async
    def change_videothread_datetime(self, id, is_start):
        try:
            videothread = VideoThread.objects.get(id=id)
            if is_start: 
                videothread.date_started = datetime.now()
            else: 
                videothread.date_ended = datetime.now()
            videothread.save()
            return videothread
        except VideoThread.DoesNotExist:
            return None


        
        
        
        
        