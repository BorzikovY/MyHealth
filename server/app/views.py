"""Import modules that work with views"""
from rest_framework import views
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated

from rest_framework.status import HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST
from rest_framework.response import Response

from app.permissions import GroupPermission, UnauthenticatedPost
from app.serializers import UserSerializer, UserLoginSerializer


class AuthToken(ObtainAuthToken):

    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'Token': f"Token {token.key}"})


class UserApi(views.APIView):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated | UnauthenticatedPost,)

    def get_serializer_context(self):
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    def get_serializer(self, *args, **kwargs):
        kwargs['context'] = self.get_serializer_context()
        return self.serializer_class(*args, **kwargs)

    def get(self, request):
        serializer = self.serializer_class(request.user)
        return Response(serializer.data)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def put(self, request):
        user = self.serializer_class().update(
            instance=request.user,
            validated_data=request.data
        )
        serializer = self.serializer_class(user)
        return Response(serializer.data)

    def delete(self, request):
        request.user.delete()
        return Response(status=HTTP_204_NO_CONTENT)
