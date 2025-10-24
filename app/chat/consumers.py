import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from chat.models import Chat, Message
from django.contrib.auth.models import User
import logging
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)





class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.user = self.scope["user"]

        self.chat = await database_sync_to_async(Chat.objects.get)(id=self.chat_id)

        # Проверяем, имеет ли пользователь доступ к чату
        if self.user != self.chat.customer and self.user != self.chat.manager:
            await self.close()
            return

        if self.user == self.chat.manager:
            await database_sync_to_async(self.update_status)("active")

        self.room_group_name = f"chat_{self.chat_id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        logger.info(f"{self.user.username} connected to chat {self.chat_id}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message')

        if not message:
            return

        new_message = await database_sync_to_async(Message.objects.create)(
            chat=self.chat,
            author=self.user,
            content=message,
        )
        await database_sync_to_async(self.update_last_message)()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': new_message.content,
                'author': self.user.username,
            }
        )

    # async def chat_message(self, event):
    #     await self.send(text_data=json.dumps({
    #         'message': event['message'],
    #         'author': event['author'],
    #     }))

    @database_sync_to_async
    def update_status(self, status):
        self.chat.status = status
        self.chat.save(update_fields=['status'])

    @database_sync_to_async
    def update_last_message(self):
        self.chat.last_message_at = timezone.now()
        self.chat.save(update_fields=['last_message_at'])