from django.urls import path

from echo import views

app_name = 'echo'

urlpatterns = [
    path('', views.index, name='index'),
    path('image/', views.echo_image, name='echo_image'),
]
