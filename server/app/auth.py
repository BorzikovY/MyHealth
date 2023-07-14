from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ValidationError

from app.models import TelegramUser


class TelegramAuthBackend(ModelBackend):
    def authenticate(self, request, telegram_id=None, chat_id=None, **kwargs):
        try:
            telegram_user: TelegramUser = TelegramUser.objects.get(telegram_id=telegram_id)
            if telegram_user.check_chat_id(chat_id):
                return telegram_user
            raise ValidationError("Chat id is incorrect")
        except TelegramUser.DoesNotExist:
            raise ValidationError(f"Telegram user with {telegram_id} id not found")

    def get_user(self, user_id):
        try:
            return TelegramUser.objects.get(pk=user_id)
        except TelegramUser.DoesNotExist:
            return None