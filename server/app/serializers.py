from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from rest_framework import serializers

from app.models import TelegramUser, Subscriber, TrainingProgram, SportNutrition


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


class InitSerializerMixin:
    def __init__(self, *args, **kwargs):
        serializers.ModelSerializer.__init__(
            self, *args, **kwargs
        )
        InstanceCreationMixin.__init__(
            self, kwargs.get("context", {})
        )


class SubscriberSerializer(serializers.ModelSerializer, InstanceCreationMixin, InitSerializerMixin):

    class Meta:
        model = Subscriber
        read_only_fields = ["id", "is_adult"]
        fields = ["id", "gender", "age", "height", "weight", "is_adult"]

    def __init__(self, *args, **kwargs):
        InitSerializerMixin.__init__(self, *args, **kwargs)

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


class UserSerializer(serializers.ModelSerializer, InstanceCreationMixin, InitSerializerMixin):
    subscriber = SubscriberSerializer(read_only=True)
    chat_id = serializers.CharField(required=True, write_only=True, max_length=128)

    def __init__(self, *args, **kwargs):
        InitSerializerMixin.__init__(self, *args, **kwargs)

    def create(self, validated_data):
        try:
            user = TelegramUser.objects.create_user(**validated_data)
        except ValueError as error:
            raise serializers.ValidationError(error) from error
        else:
            return user

    def get_instance(self, request):
        return request.user

    class Meta:
        model = TelegramUser
        read_only_fields = ("id", "balance", "subscriber")
        fields = (
            "id", "telegram_id", "chat_id", "first_name",
            "last_name", "balance", "subscriber"
        )


class NutritionSerializer(serializers.ModelSerializer, InstanceCreationMixin, InitSerializerMixin):

    def __init__(self, *args, **kwargs):
        InitSerializerMixin.__init__(self, *args, **kwargs)

    class Meta:
        model = SportNutrition
        fields = (
            "name", "description", "dosages",
            "use", "contraindications"
        )
        read_only_fields = fields


class ProgramSerializer(serializers.ModelSerializer, InstanceCreationMixin, InitSerializerMixin):
    nutrition = NutritionSerializer(read_only=True)

    def __init__(self, *args, **kwargs):
        if kwargs.get("program_id"):
            self.program_id = kwargs.pop("program_id")
        InitSerializerMixin.__init__(self, *args, **kwargs)

    def get_instance(self, request):
        if hasattr(self, "program_id"):
            return TrainingProgram.objects.get(id=self.program_id)
        return None

    def create(self, validated_data):
        subscriber = self.context["request"].user.subscriber
        subscriber.training_program = self.instance
        subscriber.save()
        return self.instance

    class Meta:
        model = TrainingProgram
        fields = (
            "name", "description", "image", "weeks",
            "avg_training_time", "training_count",
            "difficulty", "nutrition"
        )
        read_only_fields = fields


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



