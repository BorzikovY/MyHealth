"""Import modules that work with views"""
from typing import List
import coreapi

from rest_framework import views
from rest_framework import generics
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated

from rest_framework.status import HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST
from rest_framework.response import Response

from app.permissions import GroupPermission, UnauthenticatedPost, SubscribePermission, UnauthenticatedGet
from app.serializers import UserSerializer, UserLoginSerializer, SubscriberSerializer, UserUpdateSerializer, \
    ProgramSerializer


class AuthToken(ObtainAuthToken):

    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'Authorization': f"Token {token.key}"})


class RestApi(type):

    serializer_class = None
    __methods__ = ["get", "post", "put", "delete"]

    def __new__(cls, name, bases, kwargs):
        for attr_name in kwargs.get("__methods__", cls.__methods__):
            if not kwargs.get(attr_name):
                kwargs[attr_name] = getattr(cls, attr_name)
        if not kwargs.get("get_serializer_context"):
            kwargs["get_serializer_context"] = cls.get_serializer_context
        if not kwargs.get("get_serializer"):
            kwargs["get_serializer"] = cls.get_serializer

        return super(RestApi, cls).__new__(cls, name, bases, kwargs)

    def get_serializer_context(self):
        return {
            'request': getattr(self, "request"),
            'format': getattr(self, "format_kwarg"),
            'view': self
        }

    def get_serializer(self, *args, **kwargs):
        kwargs['context'] = self.get_serializer_context()
        return self.serializer_class(*args, **kwargs)

    def get(self, request, **kwargs):
        serializer = self.get_serializer(**kwargs)
        return Response(serializer.data)

    def post(self, request, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            **kwargs
        )
        if serializer.is_valid(raise_exception=True):
            serializer.create(serializer.validated_data)
            return Response(serializer.data)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def put(self, request, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            **kwargs
        )
        if serializer.is_valid(raise_exception=True):
            serializer.update(serializer.instance, serializer.validated_data)
            return Response(serializer.data)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def delete(self, request, **kwargs):
        serializer = self.get_serializer(**kwargs)
        serializer.delete()
        return Response(status=HTTP_204_NO_CONTENT)


class UserApi(generics.GenericAPIView, metaclass=RestApi):
    __methods__ = ["get", "post", "put"]
    serializer_class = UserSerializer
    update_serializer = UserUpdateSerializer
    permission_classes = (IsAuthenticated | UnauthenticatedPost,)

    def get_serializer(self, *args, **kwargs):
        kwargs['context'] = self.get_serializer_context()
        if kwargs['context']['request'].method == "PUT":
            return self.update_serializer(*args, **kwargs)
        return self.serializer_class(*args, **kwargs)


class SubscriberApi(generics.GenericAPIView, metaclass=RestApi):
    __methods__ = ["get", "post", "put", "delete"]
    serializer_class = SubscriberSerializer
    permission_classes = (IsAuthenticated,)


class ProgramApi(generics.GenericAPIView, metaclass=RestApi):
    __methods__ = ["get", "post"]
    serializer_class = ProgramSerializer
    permission_classes = (SubscribePermission | UnauthenticatedGet,)


