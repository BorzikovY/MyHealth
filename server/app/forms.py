"""Import modules that work with forms"""
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from app.models import TelegramUser


class TelegramUserCreationForm(
    UserCreationForm
):  # pylint: disable=too-many-ancestors;too-few-public-methods;

    """
    Form for creating new Telegram user
    """

    class Meta:  # pylint: disable=too-few-public-methods
        """
        Meta data
        """

        model = TelegramUser
        fields = (
            "telegram_id",
            "chat_id",
        )


class TelegramUserChangeForm(
    UserChangeForm
):  # pylint: disable=too-many-ancestors;too-few-public-methods;

    """
    Form for updating Telegram user
    """

    class Meta:  # pylint: disable=too-few-public-methods
        """
        Meta data
        """

        model = TelegramUser
        fields = (
            "telegram_id",
            "chat_id",
        )


class TelegramUserLoginForm(forms.Form):
    """
    Form for Telegram user's authorization
    """

    def __init__(self, *args, request=None, **kwargs):
        self.telegram_user, self.request = None, request
        super().__init__(self, *args, request, **kwargs)

    def clean(self):
        telegram_id = self.cleaned_data.get("telegram_id")
        chat_id = self.cleaned_data.get("chat_id")

        if telegram_id is not None and chat_id:
            self.telegram_user = authenticate(
                self.request, telegram_id=telegram_id, chat_id=chat_id
            )
        return self.cleaned_data

    def get_user(self):
        """
        @return: Telegram user instance
        """
        return self.telegram_user

    telegram_id = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "", "id": "telegram_id"}
        )
    )
    chat_id = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "",
                "id": "chat_id",
            }
        )
    )
