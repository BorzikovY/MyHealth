"""Import modules that work with views"""
from typing import Dict

from rest_framework import generics
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import ModelSerializer

from rest_framework.status import HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST
from rest_framework.response import Response

from app.permissions import (
    UnauthenticatedPost,
    SubscribePermission,
    UnauthenticatedGet,
)
from app.serializers import (
    UserSerializer,
    UserLoginSerializer,
    SubscriberSerializer,
    UserUpdateSerializer,
    ProgramSerializer,
)


class AuthToken(ObtainAuthToken):
    """
    Obtain token view
    """

    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        (
            token,
            created,  # pylint: disable=unused-variable
        ) = Token.objects.get_or_create(  # pylint: disable=no-member
            user=user
        )
        return Response({"Authorization": f"Token {token.key}"})


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
        """
        Get request
        @param request:
        @param kwargs:
        @return:
        """
        serializer = self.get_serializer(**kwargs)
        return Response(serializer.data)

    def post(self, request, **kwargs):  # pylint: disable=bad-mcs-method-argument
        """
        Post request
        @param request:
        @param kwargs:
        @return:
        """
        serializer = self.get_serializer(data=request.data, **kwargs)
        if serializer.is_valid(raise_exception=True):
            serializer.create(serializer.validated_data)
            return Response(serializer.data)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def put(self, request, **kwargs):  # pylint: disable=bad-mcs-method-argument
        """
        Put request
        @param request:
        @param kwargs:
        @return:
        """
        serializer = self.get_serializer(data=request.data, **kwargs)
        if serializer.is_valid(raise_exception=True):
            serializer.update(serializer.instance, serializer.validated_data)
            return Response(serializer.data)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def delete(
        self, request, **kwargs
    ):  # pylint: disable=bad-mcs-method-argument, unused-argument
        """
        Delete request
        @param request:
        @param kwargs:
        @return:
        """
        serializer = self.get_serializer(**kwargs)
        serializer.delete()  # pylint: disable=no-member
        return Response(status=HTTP_204_NO_CONTENT)


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

    __methods__ = ["get", "post", "put", "delete"]
    serializer_class = SubscriberSerializer
    permission_classes = (SubscribePermission | UnauthenticatedPost,)


class ProgramApi(generics.GenericAPIView, metaclass=RestApi):
    """
    Program api
    """

    __methods__ = ["get", "post"]
    serializer_class = ProgramSerializer
    permission_classes = (SubscribePermission | UnauthenticatedGet,)
