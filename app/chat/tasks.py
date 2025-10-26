from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from chat.models import models
import datetime
from django.contrib.auth.models import User
from django.conf import settings

@shared_task
def send_chat_created_email(chat_id, customer_username):
    # Получаем всех менеджеров
    managers = User.objects.filter(is_staff=True).values_list('email', flat=True)

    if not managers:
        return "Нет менеджеров для уведомления"

    subject = f"🆕 Новый чат от {customer_username}"

    # HTML и текстовая версии письма
    html_content = render_to_string("emails/chat_created.html", {
        "customer": customer_username,
        "chat_id": chat_id,
        "domain": "http://localhost:8001",  # 🔥 поменяй на свой домен/сервер
    })

    text_content = f"Клиент {customer_username} создал новый чат.\n\nПерейдите: http://localhost:8001/chat/{chat_id}/"

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=list(managers),
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()
