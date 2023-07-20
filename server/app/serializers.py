from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from rest_framework import serializers

from app.models import TelegramUser, Subscriber


class InstanceCreationMixin:
    class Meta:
        model = None
        fields = None

    def _blank(self):
        instance = self.Meta.model()
        for field in set(self.Meta.fields):
            try:
                setattr(instance, field, None)
            except AttributeError:
                pass
        return instance

    def get_instance(self, request):
        return None

    def __init__(self, context):
        request = context.get("request")
        if request:
            instance = self.get_instance(request)
            self.instance = instance if instance is not None else self._blank()
        else:
            self.instance = None


class SubscriberSerializer(serializers.ModelSerializer, InstanceCreationMixin):

    class Meta:
        model = Subscriber
        read_only_fields = ["id", "is_adult"]
        fields = ["id", "gender", "age", "height", "weight", "is_adult"]

    def __init__(self, *args, **kwargs):
        serializers.ModelSerializer.__init__(
            self, *args, **kwargs
        )
        InstanceCreationMixin.__init__(
            self, kwargs.get("context", {})
        )

    def get_instance(self, request):
        if hasattr(request.user, "subscriber"):
            subscriber = request.user.subscriber
            return subscriber
        return None

    def create(self, validated_data):
        self.instance.telegram_user = self.context["request"].user
        self.instance.save()
        return self.instance

    def delete(self):
        self.instance.delete()


class UserSerializer(serializers.ModelSerializer, InstanceCreationMixin):
    subscriber = SubscriberSerializer(read_only=True)
    chat_id = serializers.CharField(required=True, write_only=True, max_length=128)

    def __init__(self, *args, **kwargs):
        serializers.ModelSerializer.__init__(
            self, *args, **kwargs
        )
        InstanceCreationMixin.__init__(
            self, kwargs.get("context", {})
        )

    def create(self, validated_data):
        try:
            user = TelegramUser.objects.create_user(**validated_data)
        except ValueError as error:
            raise serializers.ValidationError(error) from error
        else:
            return user

    def get_instance(self, request):
        if hasattr(request, "user"):
            return request.user
        return None

    class Meta:
        model = TelegramUser
        read_only_fields = ("id", "balance")
        fields = (
            "id", "telegram_id", "chat_id", "first_name",
            "last_name", "balance", "subscriber"
        )


class UserUpdateSerializer(UserSerializer):
    class Meta:
        model = TelegramUser
        fields = ("first_name", "last_name")


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



