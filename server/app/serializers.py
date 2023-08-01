"""Import modules to work with serializers"""
from abc import abstractmethod

from django.db import transaction
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.core.exceptions import ValidationError
from django.db.models import Model
from rest_framework.serializers import (
    ModelSerializer,
    ValidationError as SerializerError,
    CharField,
    Serializer
)
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from app.models import (
    TelegramUser,
    Subscriber,
    TrainingProgram,
    SportNutrition,
    Training,
    Portion,
    Exercise,
    TrainingProgramGroup
)


class InstanceCreationMixin:  # pylint: disable=too-few-public-methods
    """
    Creates instance of model during initialization
    """

    def __init__(self, context):
        request = context.get("request")
        if request:
            instance = self.get_instance(request)
            self.instance = instance if instance is not None else self._blank()
        else:
            self.instance = None

    def _blank(self) -> Model:
        instance = self.Meta.model()
        for field in set(self.Meta.fields):
            try:
                setattr(instance, field, None)
            except AttributeError:
                pass
            except TypeError:
                pass
        return instance

    @abstractmethod
    def get_instance(self, request) -> Model | None:
        """
        Override this method to specify getting
        instance object for each model serializer
        @param request:
        @return:
        """
        return None

    class Meta:  # pylint: disable=too-few-public-methods
        """Meta class"""

        model = Model
        fields = []


class InitSerializerMixin:  # pylint: disable=too-few-public-methods
    """
    Class which contain initialization logic for each model serializer
    """

    def __init__(self, *args, **kwargs):
        ModelSerializer.__init__(  # pylint: disable=non-parent-init-called
            self, *args, **kwargs
        )
        InstanceCreationMixin.__init__(  # pylint: disable=non-parent-init-called
            self, kwargs.get("context", {})
        )


class SubscriberSerializer(ModelSerializer, InstanceCreationMixin, InitSerializerMixin):
    """
    Subscriber model serializer
    """

    def __init__(self, *args, **kwargs):  # pylint: disable=super-init-not-called
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
        """Delete instance function"""
        self.instance.delete()

    class Meta:  # pylint: disable=too-few-public-methods
        """Meta class"""

        model = Subscriber
        fields = (
            "id",
            "gender",
            "age",
            "height",
            "weight",
            "is_adult",
            "training_program",
            "sport_nutrition"
        )
        read_only_fields = fields


class UserSerializer(ModelSerializer, InstanceCreationMixin, InitSerializerMixin):
    """
    User model serializer
    """

    chat_id = CharField(required=True, write_only=True, max_length=128)

    def __init__(self, *args, **kwargs):  # pylint: disable=super-init-not-called
        InitSerializerMixin.__init__(self, *args, **kwargs)

    def create(self, validated_data):
        try:
            user = TelegramUser.objects.create_user(**validated_data)
        except ValueError as error:
            raise SerializerError(error) from error

        self.instance = user
        return user

    def get_instance(self, request):
        return request.user

    class Meta:  # pylint: disable=too-few-public-methods
        """Meta class"""

        model = TelegramUser
        read_only_fields = ("id", "balance", "subscriber")
        fields = (
            "id",
            "telegram_id",
            "chat_id",
            "first_name",
            "last_name",
            "balance",
            "subscriber"
        )


class PortionSerializer(ModelSerializer):
    """
    Portion model serializer
    """
    class Meta:
        model = Portion
        fields = (
            "id",
            "name",
            "description",
            "calories",
            "proteins",
            "fats",
            "carbs"
        )
        read_only_fields = fields


class NutritionSerializer(ModelSerializer, InstanceCreationMixin, InitSerializerMixin):
    """
    Nutrition model serializer
    """

    portions = PortionSerializer(many=True, read_only=True)

    def __init__(self, *args, **kwargs):  # pylint: disable=super-init-not-called
        if kwargs.get("nutrition_id"):
            self.nutrition_id = kwargs.pop("nutrition_id")
        InitSerializerMixin.__init__(self, *args, **kwargs)

    def get_instance(self, request):
        if hasattr(self, "nutrition_id"):
            query = SportNutrition.objects.filter(id=self.nutrition_id)
            return query.first()
        return None

    class Meta:  # pylint: disable=too-few-public-methods
        """Meta class"""

        model = SportNutrition
        fields = (
            "id",
            "name",
            "description",
            "price",
            "dosages",
            "use",
            "contraindications",
            "portions"
        )
        read_only_fields = fields


class ExerciseSerializer(ModelSerializer, InstanceCreationMixin, InitSerializerMixin):
    """
    Exercise model serializer
    """

    def __init__(self, *args, **kwargs):  # pylint: disable=super-init-not-called
        if kwargs.get("exercise_id"):
            self.exercise_id = kwargs.pop("exercise_id")
        InitSerializerMixin.__init__(self, *args, **kwargs)

    def get_instance(self, request):
        if hasattr(self, "exercise_id"):
            query = Exercise.objects.filter(id=self.exercise_id)
            return query.first()
        return None

    class Meta:  # pylint: disable=too-few-public-methods
        """Meta class"""

        model = Exercise
        fields = (
            "id",
            "name",
            "description",
            "image",
            "video"
        )
        read_only_fields = fields


class TrainingSerializer(ModelSerializer, InstanceCreationMixin, InitSerializerMixin):
    """
    Training model serializer
    """

    def __init__(self, *args, **kwargs):  # pylint: disable=super-init-not-called
        if kwargs.get("training_id"):
            self.training_id = kwargs.pop("training_id")
        InitSerializerMixin.__init__(self, *args, **kwargs)

    def get_instance(self, request):
        if hasattr(self, "training_id"):
            query = Training.objects.filter(id=self.training_id)
            return query.first()
        return None

    class Meta:  # pylint: disable=too-few-public-methods
        """Meta class"""

        model = Training
        fields = (
            "id",
            "name",
            "description",
            "difficulty",
            "time",
            "approach_count"
        )
        read_only_fields = fields


class ProgramGroupSerializer(ModelSerializer):
    class Meta:  # pylint: disable=too-few-public-methods
        """Meta class"""

        model = TrainingProgramGroup
        fields = (
            "id",
            "name",
            "description"
        )
        read_only_fields = fields


class ProgramSerializer(ModelSerializer, InstanceCreationMixin, InitSerializerMixin):
    """
    Program model serializer
    """
    group = ProgramGroupSerializer(read_only=True)
    trainings = TrainingSerializer(read_only=True, many=True)

    def __init__(self, *args, **kwargs):  # pylint: disable=super-init-not-called
        if kwargs.get("program_id"):
            self.program_id = kwargs.pop("program_id")
        InitSerializerMixin.__init__(self, *args, **kwargs)

    def get_instance(self, request):
        if hasattr(self, "program_id"):
            query = TrainingProgram.objects.filter(id=self.program_id)
            return query.first()
        return None

    class Meta:  # pylint: disable=too-few-public-methods
        """Meta class"""

        model = TrainingProgram
        fields = (
            "id",
            "name",
            "description",
            "price",
            "image",
            "weeks",
            "avg_training_time",
            "training_count",
            "difficulty",
            "group",
            "trainings"
        )
        read_only_fields = fields


class UserUpdateSerializer(UserSerializer):  # pylint: disable=too-many-ancestors
    """
    User update serializer
    """

    class Meta:  # pylint: disable=too-few-public-methods
        """Meta class"""

        model = TelegramUser
        fields = (
            "id",
            "telegram_id",
            "first_name",
            "last_name"
            "balance"
        )
        read_only_field = ["id", "telegram_id"]


class SubscriberUpdateSerializer(SubscriberSerializer):  # pylint: disable=too-many-ancestors
    """
    User update serializer
    """
    def update(self, instance, validated_data: dict):
        for personal_field in ("age", "height", "weight", "gender"):
            setattr(instance, personal_field, validated_data.get(personal_field))
        instance.save()
        for private_field in ("training_program", "sport_nutrition"):
            with transaction.atomic():
                try:
                    content = validated_data.get(private_field)
                    telegram_user = self.instance.telegram_user
                    if content is not None and getattr(self.instance, private_field) != content:
                        telegram_user.cash -= content.price
                        setattr(self.instance, private_field, content)
                        instance.save()
                        telegram_user.save()
                except ValidationError as error:
                    raise SerializerError(error.message) from error

    class Meta:  # pylint: disable=too-few-public-methods
        """Meta class"""

        model = Subscriber
        fields = (
            "id",
            "age",
            "height",
            "weight",
            "gender",
            "training_program",
            "sport_nutrition"
        )
        read_only_fields = ["id",]


class UserLoginSerializer(Serializer):  # pylint: disable=abstract-method
    """
    User login serializer
    """

    telegram_id = CharField(max_length=32, required=True)
    chat_id = CharField(required=True, write_only=True, max_length=128)

    def validate(self, attrs):
        try:
            user = authenticate(self.context["request"], **attrs)
            refresh = RefreshToken.for_user(user)

            if api_settings.UPDATE_LAST_LOGIN:
                update_last_login(None, user)

            return {
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            }
        except ValidationError as error:
            raise SerializerError(error.message) from error
