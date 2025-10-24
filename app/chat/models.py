from django.db import models

from django.contrib.auth.models import User

STATUS_CHOICES = [
    ('new', 'Новый'),
    ('active', 'В работе'),
    ('closed', 'Закрыт'),
]

class Chat(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customer_chats')
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='manager_chats')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='new')
    last_message_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat {self.id} ({self.customer.username})"

class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.author.username} in Chat {self.chat.id}: {self.content}"