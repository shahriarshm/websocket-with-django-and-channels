from django.contrib import admin
from chat.models import Member, GroupChat, Message, VideoThread

# Register your models here.
admin.site.register(Member)
admin.site.register(GroupChat)
admin.site.register(Message)
admin.site.register(VideoThread)