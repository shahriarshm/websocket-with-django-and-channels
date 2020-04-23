from django.shortcuts import render, HttpResponse
from django.utils.safestring import mark_safe
import json

# Create your views here.
def index(request):
    return render(request, 'echo/index.html')

def echo_image(request):
    return render(request, 'echo/echo_image.html')

