"""Import base user manager module"""
from django.contrib.auth.base_user import BaseUserManager


class TelegramUserManager(BaseUserManager):
    """
    Telegram user manager
    """

    def create_user(self, telegram_id, chat_id, **extra_fields):
        """
        Telegram user creation logic
        @param telegram_id:
        @param chat_id:
        @param extra_fields:
        @return: Telegram user
        """
        if not (telegram_id and chat_id):
            raise ValueError("You must specify both telegram_id and chat_id to proceed")
        telegram_user = self.model(telegram_id=telegram_id, **extra_fields)
        telegram_user.set_chat_id(chat_id)
        telegram_user.save()

        return telegram_user

    def create_superuser(self, telegram_id, chat_id, **extra_fields):
        """
        Superuser creation logic
        @param telegram_id:
        @param chat_id:
        @param extra_fields:
        @return: Telegram user
        """

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")
        return self.create_user(telegram_id, chat_id, **extra_fields)
