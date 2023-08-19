"""Import modules that work with forms"""
from typing import Dict

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from app.models import TelegramUser


class TelegramUserCreationForm(
    UserCreationForm
):  # pylint: disable=too-many-ancestors;too-few-public-methods;

    """
    Form for creating new Telegram users
    """

    class Meta:  # pylint: disable=too-few-public-methods
        """Meta class"""

        model = TelegramUser
        fields = (
            "telegram_id",
            "chat_id",
        )


class TelegramUserChangeForm(
    UserChangeForm
):  # pylint: disable=too-many-ancestors;too-few-public-methods;

    """
    Form for updating Telegram users
    """

    class Meta:  # pylint: disable=too-few-public-methods
        """Meta class"""

        model = TelegramUser
        fields = (
            "telegram_id",
            "chat_id",
        )

    def save(self, commit=True) -> TelegramUser:
        telegram_user = super(  # pylint: disable=super-with-arguments
            TelegramUserChangeForm, self
        ).save(commit=False)

        telegram_id, chat_id = [
            self.cleaned_data.get(key) for key in ["telegram_id", "chat_id"]
        ]

        if not TelegramUser.objects.filter(id=telegram_user.id).exists():
            telegram_user.set_chat_id(chat_id)
        telegram_user.save()

        return telegram_user


class TelegramUserLoginForm(forms.Form):
    """
    Form for Telegram user's authorization
    """

    def __init__(self, *args, request=None, **kwargs):
        self.telegram_user = None
        self.request = request

        super(  # pylint: disable=super-with-arguments
            TelegramUserLoginForm, self
        ).__init__(*args, **kwargs)

        self.fields["password"].label = "Chat id"
        self.fields["username"].label = "Telegram id"

    def clean(self) -> Dict:
        telegram_id = self.cleaned_data.get("username")
        chat_id = self.cleaned_data.get("password")

        if telegram_id is not None and chat_id:
            self.telegram_user = authenticate(
                self.request, telegram_id=telegram_id, chat_id=chat_id
            )
        return self.cleaned_data

    def get_user(self) -> TelegramUser | None:
        """
        @return: Telegram user instance
        """
        return self.telegram_user

    username = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "", "id": "telegram_id"}
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "", "id": "chat_id"}
        )
    )
