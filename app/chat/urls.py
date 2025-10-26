from django.urls import path
from django.contrib.auth.views import TemplateView
from chat.views import ChatListView, ChatRoomView, start_chat, close_chat

urlpatterns = [
    path('support/', start_chat, name='start_chat'),
    path ('chat_list/', ChatListView.as_view(), name='chat_list'),
    path('chat/<int:chat_id>/', ChatRoomView.as_view(), name='chat_room'),
    path('chat/close/<int:chat_id>/', close_chat, name='close_chat')
]