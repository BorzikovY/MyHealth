from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm

from app.models import TelegramUser


class TelegramUserCreationForm(UserCreationForm):
    class Meta:
        model = TelegramUser
        fields = ("telegram_id", "chat_id",)


class TelegramUserChangeForm(UserChangeForm):
    class Meta:
        model = TelegramUser
        fields = ("telegram_id", "chat_id",)


class TelegramUserLoginForm(forms.Form):

    def __init__(self, request=None, *args, **kwargs):
        self.telegram_user, self.request = None, request
        super(TelegramUserLoginForm, self).__init__(*args, **kwargs)

    def clean(self):
        telegram_id = self.cleaned_data.get("telegram_id")
        chat_id = self.cleaned_data.get("chat_id")

        if telegram_id is not None and chat_id:
            self.telegram_user = authenticate(
                self.request, telegram_id=telegram_id, chat_id=chat_id
            )
        return self.cleaned_data

    def get_user(self):
        return self.telegram_user

    telegram_id = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': '', 'id': 'telegram_id'}))
    chat_id = forms.CharField(widget=forms.PasswordInput(
        attrs={
            'class': 'form-control',
            'placeholder': '',
            'id': 'chat_id',
        }
    ))
