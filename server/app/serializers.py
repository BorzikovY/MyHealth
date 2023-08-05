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
    Serializer,
    PrimaryKeyRelatedField
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
    TrainingProgramGroup,
    Approach
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
    telegram_id = CharField(read_only=True, source="telegram_user.telegram_id")

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
            "telegram_id",
            "gender",
            "age",
            "height",
            "weight",
            "training_program",
            "sport_nutrition"
        )
        read_only_fields = fields


class UserSerializer(ModelSerializer, InstanceCreationMixin, InitSerializerMixin):
    """
    User model serializer
    """

    chat_id = CharField(required=True, write_only=True, max_length=128)
    subscriber = SubscriberSerializer(read_only=True)

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
        read_only_fields = ("balance", "subscriber")
        fields = (
            "telegram_id",
            "chat_id",
            "first_name",
            "last_name",
            "balance",
            "subscriber"
        )


class PortionSerializer(ModelSerializer, InstanceCreationMixin, InitSerializerMixin):
    """
    Portion model serializer
    """

    nutritions = PrimaryKeyRelatedField(many=True, read_only=True)

    def __init__(self, *args, **kwargs):  # pylint: disable=super-init-not-called
        if kwargs.get("portion_id") is not None:
            self.portion_id = kwargs.pop("portion_id")
        InitSerializerMixin.__init__(self, *args, **kwargs)

    def get_instance(self, request):
        if hasattr(self, "portion_id"):
            query = Portion.objects.filter(id=self.portion_id)
            return query.first()
        return None

    class Meta:
        model = Portion
        fields = (
            "id",
            "name",
            "description",
            "calories",
            "proteins",
            "fats",
            "carbs",
            "nutritions"
        )
        read_only_fields = fields


class NutritionSerializer(ModelSerializer, InstanceCreationMixin, InitSerializerMixin):
    """
    Nutrition model serializer
    """

    def __init__(self, *args, **kwargs):  # pylint: disable=super-init-not-called
        if kwargs.get("nutrition_id") is not None:
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
        )
        read_only_fields = fields


class ExerciseSerializer(ModelSerializer):
    class Meta:  # pylint: disable=too-few-public-methods
        """Meta class"""

        model = Exercise
        fields = (
            "name",
            "description",
            "image",
            "video"
        )
        read_only_fields = fields


class ApproachSerializer(ModelSerializer, InstanceCreationMixin, InitSerializerMixin):
    """
    Exercise model serializer
    """

    exercise = ExerciseSerializer(read_only=True)

    def __init__(self, *args, **kwargs):  # pylint: disable=super-init-not-called
        if kwargs.get("approach_id") is not None:
            self.approach_id = kwargs.pop("approach_id")
        InitSerializerMixin.__init__(self, *args, **kwargs)

    def get_instance(self, request):
        if hasattr(self, "approach_id"):
            query = Approach.objects.filter(id=self.approach_id)
            return query.first()
        return None

    class Meta:  # pylint: disable=too-few-public-methods
        """Meta class"""

        model = Approach
        fields = (
            "id",
            "time",
            "repetition_count",
            "rest",
            "training",
            "exercise"
        )
        read_only_fields = fields


class TrainingSerializer(ModelSerializer, InstanceCreationMixin, InitSerializerMixin):
    """
    Training model serializer
    """

    programs = PrimaryKeyRelatedField(many=True, read_only=True)

    def __init__(self, *args, **kwargs):  # pylint: disable=super-init-not-called
        if kwargs.get("training_id") is not None:
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
            "approach_count",
            "programs"
        )
        read_only_fields = fields


class ProgramGroupSerializer(ModelSerializer):
    class Meta:  # pylint: disable=too-few-public-methods
        """Meta class"""

        model = TrainingProgramGroup
        fields = (
            "name",
            "description"
        )
        read_only_fields = fields


class ProgramSerializer(ModelSerializer, InstanceCreationMixin, InitSerializerMixin):
    """
    Program model serializer
    """
    group = ProgramGroupSerializer(read_only=True)

    def __init__(self, *args, **kwargs):  # pylint: disable=super-init-not-called
        if kwargs.get("program_id") is not None:
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
            "group"
        )
        read_only_fields = fields


class SubscriberUpdateSerializer(SubscriberSerializer):  # pylint: disable=too-many-ancestors
    """
    Subscribe update serializer
    """

    telegram_id = CharField(read_only=True, source="telegram_user.telegram_id")

    class Meta:  # pylint: disable=too-few-public-methods
        """Meta class"""

        model = Subscriber
        fields = (
            "telegram_id",
            "age",
            "height",
            "weight",
            "gender",
            "training_program",
            "sport_nutrition"
        )


class UserUpdateSerializer(UserSerializer):  # pylint: disable=too-many-ancestors
    """
    User update serializer
    """

    subscriber = SubscriberUpdateSerializer()

    @staticmethod
    def update_simple(obj: Model, fields: list[str], data: dict):
        for field in fields:
            if value := data.get(field):
                setattr(obj, field, value)
        obj.save()

    def update_business(self, obj: Model, fields: list[str], data: dict):
        for field in fields:
            with transaction.atomic():
                try:
                    content = data.get(field)
                    if getattr(obj, field) != content and content is not None:
                        self.instance.cash -= content.price
                        setattr(obj, field, content)
                        self.instance.save()
                        obj.save()
                except ValidationError as error:
                    raise SerializerError(error.message) from error

    def update(self, instance, validated_data):
        self.update_simple(instance, ["first_name", "last_name"], validated_data)
        if (subscriber_data := validated_data.get("subscriber")) and hasattr(instance, "subscriber"):
            self.update_simple(
                instance.subscriber,
                ["gender", "height", "weight", "age"],
                subscriber_data
            )
            self.update_business(
                instance.subscriber,
                ["sport_nutrition", "training_program"],
                subscriber_data
            )

    class Meta:  # pylint: disable=too-few-public-methods
        """Meta class"""

        model = TelegramUser
        fields = (
            "telegram_id",
            "first_name",
            "last_name",
            "balance",
            "subscriber"
        )
        read_only_fields = ("telegram_id", "balance")


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
