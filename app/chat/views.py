from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from chat.models import Chat, Message
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseForbidden
from django.views import View
from django.shortcuts import render, redirect
from django.db import models

@login_required
def start_chat(request):
    # Ищем активный чат для пользователя
    active_chat = Chat.objects.filter(customer=request.user, status="active").first()

    if active_chat:
        chat = active_chat
    else:
        # Создаём новый чат, если активного нет
        chat, created = Chat.objects.get_or_create(
            customer=request.user,
            manager=None,
            defaults={"status": "new"}
        )

    return redirect("chat_room", chat_id=int(chat.id))

@login_required
def close_chat(request, chat_id):

    chat = get_object_or_404(Chat, id=chat_id)
    if chat.manager == request.user:
        chat.status = "closed"
        chat.save()
        chats = Chat.objects.all().order_by(
            models.Case(
                models.When(status='new', then=0),
                models.When(status='active', then=1),
                models.When(status='closed', then=2),
                output_field=models.IntegerField(),
            ),
            '-last_message_at',
        )
        return render(request, "chat/chat_list.html", {"chats": chats})
    else:
        return HttpResponseForbidden("У вас нет доступа к данному чату")

class ChatRoomView(View):
    def get(self, request, chat_id):
        chat = get_object_or_404(Chat, id=chat_id)

        if chat.manager is None and request.user.is_superuser:
            chat.manager = request.user
            chat.status = "active"
            chat.save()
        elif chat.customer != request.user and chat.manager != request.user and request.user.is_superuser:
            return HttpResponseForbidden("Этот чат занят другим оператором.")
        elif chat.customer != request.user and not request.user.is_superuser:
            return HttpResponseForbidden("У вас нет доступа к данному чату")

        messages = Message.objects.filter(chat=chat).order_by("timestamp")
        return render(request, "chat/chat_room.html", {"chat": chat, "messages": messages})


class ChatListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Chat
    template_name = 'chat/chat_list.html'
    context_object_name = 'chats'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        return HttpResponseForbidden("У вас нет доступа к списку чатов.")

    def get_queryset(self):
        # Показываем все чаты, отсортированные по последнему сообщению
        return Chat.objects.all().order_by(
            models.Case(
                models.When(status='new', then=0),
                models.When(status='active', then=1),
                models.When(status='closed', then=2),
                output_field=models.IntegerField(),
            ),
            '-last_message_at',
        )