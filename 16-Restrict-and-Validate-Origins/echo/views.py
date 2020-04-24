from django.shortcuts import render, HttpResponse
from django.utils.safestring import mark_safe
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Create your views here.
def index(request):
    return render(request, 'echo/index.html')

def echo_image(request):
    return render(request, 'echo/echo_image.html')

def join_chat(request, username):
    return render(request, 'echo/join_chat.html', {'username_json': mark_safe(json.dumps(username))})

def new_message(request, username):
    receiver = request.GET['receiver']
    text = request.GET['text']
    channel_layer = get_channel_layer()
    group_name = f"chat_{receiver}"

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'chat_message',
            'message': json.dumps({'sender': username, 'receiver': receiver, 'text': text})
        }
    )

    return HttpResponse('Message Sent')
