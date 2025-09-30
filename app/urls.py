from django.urls import path
from . import views

urlpatterns = [
    path('', views.modes_page, name='modes_page'),
    path('chat/', views.chat_page, name='chat_page'),
    path('api/chat/', views.chat_api, name='chat_api'),
    path('api/modes/', views.list_modes, name='list_modes'),
]


