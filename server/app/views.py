"""Import modules that work with views"""
from typing import Dict

from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import ModelSerializer

from rest_framework.status import (
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_200_OK,
    HTTP_201_CREATED
)
from rest_framework.response import Response

from app.filters import (
    ProgramFilterBackend,
    NutritionFilterBackend,
    TrainingFilterBackend,
    ApproachFilterBackend,
    PortionFilterBackend,
    duration,
    DataFilter,
)
from app.models import TrainingProgram, SportNutrition, Training, Approach, Portion
from app.permissions import (
    UnauthenticatedPost,
    AuthenticatedPost,
    SubscribePermission,
    GroupPermission,
    OwnerPermission
)
from app.serializers import (
    UserSerializer,
    SubscriberSerializer,
    UserUpdateSerializer,
    ProgramSerializer,
    NutritionSerializer,
    TrainingSerializer,
    ApproachSerializer,
    PortionSerializer
)


class RestApi(type):
    """
    Rest api arhitecture
    """

    serializer_class = ModelSerializer
    __methods__ = ["get", "post", "put", "delete"]

    def __new__(mcs, name, bases, kwargs):
        for attr_name in kwargs.get("__methods__", mcs.__methods__):
            if not kwargs.get(attr_name):
                kwargs[attr_name] = getattr(mcs, attr_name)
        if not kwargs.get("get_serializer_context"):
            kwargs["get_serializer_context"] = mcs.get_serializer_context
        if not kwargs.get("get_serializer"):
            kwargs["get_serializer"] = mcs.get_serializer

        return super(RestApi, mcs).__new__(mcs, name, bases, kwargs)

    def get_serializer_context(cls) -> Dict:
        """
        Get serializer context
        @return:
        """
        return {
            "request": getattr(cls, "request"),
            "format": getattr(cls, "format_kwarg"),
            "view": cls,
        }

    def get_serializer(
            cls, *args, **kwargs
    ) -> ModelSerializer:  # pylint: disable=no-value-for-parameter
        """
        Get serializer with context
        @param args:
        @param kwargs:
        @return:
        """
        kwargs[
            "context"
        ] = cls.get_serializer_context()  # pylint: disable=no-value-for-parameter
        return cls.serializer_class(*args, **kwargs)

    def get(
            self, request, **kwargs
    ):  # pylint: disable=unused-argument, bad-mcs-method-argument
        serializer = self.get_serializer(**kwargs)
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request, **kwargs):  # pylint: disable=bad-mcs-method-argument
        serializer = self.get_serializer(data=request.data, **kwargs)
        if serializer.is_valid(raise_exception=True):
            serializer.create(serializer.validated_data)
            return Response(serializer.data, status=HTTP_201_CREATED)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def put(self, request, **kwargs):  # pylint: disable=bad-mcs-method-argument
        serializer = self.get_serializer(data=request.data, **kwargs)
        if serializer.is_valid(raise_exception=True):
            serializer.update(serializer.instance, serializer.validated_data)
            return Response(serializer.data, status=HTTP_200_OK)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def delete(
            self, request, **kwargs
    ):  # pylint: disable=bad-mcs-method-argument, unused-argument
        serializer = self.get_serializer(**kwargs)
        serializer.delete()  # pylint: disable=no-member
        return Response(status=HTTP_204_NO_CONTENT)


"""
Client APIs - available for any telegram user
"""


class UserApi(generics.GenericAPIView, metaclass=RestApi):
    """
    User api
    """

    __methods__ = ["get", "post", "put"]
    serializer_class = UserSerializer
    update_serializer = UserUpdateSerializer
    permission_classes = (IsAuthenticated | UnauthenticatedPost,)

    def get_serializer(self, *args, **kwargs):
        kwargs["context"] = self.get_serializer_context()
        if kwargs["context"]["request"].method == "PUT":
            return self.update_serializer(*args, **kwargs)
        return self.serializer_class(*args, **kwargs)


class SubscriberApi(generics.GenericAPIView, metaclass=RestApi):
    """
    Subscriber api
    """

    __methods__ = ["post", "delete"]
    serializer_class = SubscriberSerializer
    permission_classes = (SubscribePermission | AuthenticatedPost,)


class ProgramApi(generics.GenericAPIView, metaclass=RestApi):
    """
    Program api
    """

    __methods__ = ["get"]
    serializer_class = ProgramSerializer
    permission_classes = (IsAuthenticated,)


class NutritionApi(generics.GenericAPIView, metaclass=RestApi):
    """
    Nutrition api
    """

    __methods__ = ["get"]
    serializer_class = NutritionSerializer
    permission_classes = (IsAuthenticated,)


class TrainingApi(generics.GenericAPIView, metaclass=RestApi):
    """
    Training api
    """

    __methods__ = ["get"]
    serializer_class = TrainingSerializer
    permission_classes = (IsAuthenticated,)


class ApproachApi(generics.GenericAPIView, metaclass=RestApi):
    """
    Approach api
    """

    __methods__ = ["get"]
    serializer_class = ApproachSerializer
    permission_classes = (OwnerPermission,)


class PortionApi(generics.GenericAPIView, metaclass=RestApi):
    """
    Portion api
    """

    __methods__ = ["get"]
    serializer_class = ApproachSerializer
    permission_classes = (IsAuthenticated,)


"""
Admin APIs - available for staff (only)
"""


class ProgramListApi(viewsets.ModelViewSet):
    serializer_class = ProgramSerializer
    filter_backends = (ProgramFilterBackend,)
    permission_classes = (GroupPermission(groups=["Staff"]),)
    queryset = TrainingProgram.objects.all()

    def filter_queryset(self, queryset):
        first_filter = DataFilter.filter(
            self.request.query_params.get('difficulty'),
            data_class=float
        )
        second_filter = DataFilter.filter(
            self.request.query_params.get('weeks'),
            data_class=int
        )

        queryset = filter(
            lambda note: first_filter(note.difficulty) and second_filter(note.weeks),
            TrainingProgram.objects.all()
        )

        return queryset


class NutritionListApi(viewsets.ModelViewSet):
    serializer_class = NutritionSerializer
    filter_backends = (NutritionFilterBackend,)
    permission_classes = (GroupPermission(groups=["Staff"]),)
    queryset = SportNutrition.objects.all()

    def filter_queryset(self, queryset):
        first_filter = DataFilter.filter(
            self.request.query_params.get('dosages'),
            data_class=str
        )
        second_filter = DataFilter.filter(
            self.request.query_params.get('use'),
            data_class=str
        )
        third_filter = DataFilter.filter(
            self.request.query_params.get('contraindications'),
            data_class=str
        )

        queryset = filter(
            lambda note:
            first_filter(note.dosages)
            and second_filter(note.use)
            and third_filter(note.contraindications),
            SportNutrition.objects.all()
        )

        return queryset


class TrainingListApi(viewsets.ModelViewSet):
    serializer_class = TrainingSerializer
    filter_backends = (TrainingFilterBackend,)
    permission_classes = (GroupPermission(groups=["Staff"]),)
    queryset = Training.objects.all()

    def filter_queryset(self, queryset):
        program_id = self.request.query_params.get('program_id')
        first_filter = DataFilter.filter(
            self.request.query_params.get('difficulty'),
            data_class=float
        )
        second_filter = DataFilter.filter(
            self.request.query_params.get('time'),
            data_class=duration
        )
        instances = TrainingProgram.objects.filter(id=program_id)[:1]
        filter_data = {"training_program_set": instances} if instances else {}
        queryset = filter(
            lambda note:
            first_filter(note.difficulty)
            and second_filter(note.time),
            Training.objects.filter(
                *filter_data
            )
        )

        return queryset


class PortionListApi(viewsets.ModelViewSet):
    serializer_class = PortionSerializer
    filter_backends = (PortionFilterBackend,)
    permission_classes = (GroupPermission(groups=["Staff"]),)
    queryset = Portion.objects.all()

    def filter_queryset(self, queryset):
        nutrition_id = self.request.query_params.get('nutrition_id')
        instance = SportNutrition.objects.filter(id=nutrition_id).first()
        filter_data = {"training": instance} if instance else {}
        queryset = Portion.objects.filter(
            **filter_data
        )
        return queryset


class ApproachListApi(viewsets.ModelViewSet):
    serializer_class = ApproachSerializer
    filter_backends = (ApproachFilterBackend,)
    permission_classes = (OwnerPermission,)
    queryset = Approach.objects.all()

    def filter_queryset(self, queryset):
        training_id = self.request.query_params.get('training_id')
        instance = Training.objects.filter(id=training_id).first()
        filter_data = {"training": instance} if instance else {}
        queryset = Approach.objects.filter(
            **filter_data
        ).order_by("query_place")

        return queryset
