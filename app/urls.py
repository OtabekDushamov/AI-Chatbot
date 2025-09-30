from django.urls import path
from . import views

urlpatterns = [
    path('', views.modes_page, name='modes_page'),
    path('chat/create/', views.create_chat, name='create_chat'),
    path('chat/<int:chat_id>/', views.chat_detail, name='chat_detail'),
    path('api/chat/', views.chat_api, name='chat_api'),
    path('api/modes/', views.list_modes, name='list_modes'),
]


