"""Import modules that work with views"""
from rest_framework import viewsets


from app.models import TelegramUser
from app.serializers import TelegramUserSerializer


class TelegramUserViewSet(viewsets.ModelViewSet):
    queryset = TelegramUser.objects.all()
    serializer_class = TelegramUserSerializer
