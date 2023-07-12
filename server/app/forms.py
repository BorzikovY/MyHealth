from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from django.contrib.auth import get_user_model


class TelegramUserCreationForm(UserCreationForm):

    class Meta:
        model = get_user_model()
        fields = ("telegram_id", "chat_id",)


class TelegramUserChangeForm(UserChangeForm):

    class Meta:
        model = get_user_model()
        fields = ("telegram_id", "chat_id",)