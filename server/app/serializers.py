from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from rest_framework import serializers

from app.models import TelegramUser, Subscriber


class SubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscriber
        read_only_fields = ("id", "is_adult")
        fields = ("id", "gender", "age", "height", "weight", "is_adult")


class UserSerializer(serializers.ModelSerializer):
    subscriber = SubscriberSerializer(read_only=True)
    chat_id = serializers.CharField(required=True, write_only=True, max_length=128)

    def create(self, validated_data):
        user = TelegramUser.objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        first_name = "first_name", validated_data.get("first_name", None)
        last_name = "last_name", validated_data.get("last_name", None)
        for field, value in filter(lambda item: item[1] is not None,
                                   [first_name, last_name]):
            setattr(instance, field, value)
        instance.save()
        return instance

    class Meta:
        model = TelegramUser
        read_only_fields = ("id", "balance")
        fields = (
            "id", "telegram_id", "chat_id", "first_name",
            "last_name", "balance", "subscriber"
        )


class UserLoginSerializer(serializers.Serializer):
    telegram_id = serializers.CharField(max_length=32, required=True)
    chat_id = serializers.CharField(required=True, write_only=True, max_length=128)

    def validate(self, data):
        try:
            user = authenticate(self.context["request"], **data)
        except ValidationError as error:
            raise serializers.ValidationError(error.message)
        else:
            return {"user": user}



