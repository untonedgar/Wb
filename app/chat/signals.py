from django.db.models.signals import post_save
from django.dispatch import receiver
from chat.models import *

from chat.tasks import send_chat_created_email

@receiver(post_save, sender=Chat)
def chat_created(sender, instance, created, **kwargs):
    if created:
        send_chat_created_email.apply_async(args=[instance.id, instance.customer.username])