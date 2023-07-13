from django.contrib.auth.backends import ModelBackend
from app.models import TelegramUser


class TelegramAuthBackend(ModelBackend):
    def authenticate(self, request, telegram_id=None, chat_id=None, **kwargs):
        try:
            telegram_user: TelegramUser = TelegramUser.objects.get(telegram_id=telegram_id)
            if telegram_user.check_chat_id(chat_id):
                return telegram_user
        except TelegramUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return TelegramUser.objects.get(pk=user_id)
        except TelegramUser.DoesNotExist:
            return None