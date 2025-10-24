from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from chat.models import Chat
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseForbidden
from django.views import View
from django.shortcuts import render, redirect
from django.db import models

def start_chat(request):
    # Ищем или создаём чат, где этот пользователь клиент, а менеджер ещё не назначен
    chat, created = Chat.objects.get_or_create(
        customer=request.user,
        manager=None,
        defaults={"status": "new"}
    )
    # Перенаправляем пользователя в комнату чата
    return redirect("chat_room", chat_id=chat.id)

class ChatRoomView(View):
    def get(self, request, chat_id):
        chat = get_object_or_404(Chat, id=chat_id)

        if chat.manager is None:
            chat.manager = request.user
            chat.status = "active"
            chat.save()
        elif chat.manager != request.user:
            return HttpResponseForbidden("Этот чат занят другим оператором.")

        return render(request, "chat/chat_room.html", {"chat": chat})


class ChatListView(LoginRequiredMixin, ListView):
    model = Chat
    template_name = 'chat/chat_list.html'
    context_object_name = 'chats'

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
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