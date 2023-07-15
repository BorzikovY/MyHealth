from rest_framework import serializers

from app.models import TelegramUser


class TelegramUserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = TelegramUser
        fields = ['first_name', 'last_name', 'balance']