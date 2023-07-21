"""Imports that work with urls"""
from django.urls import path, include
from rest_framework.permissions import AllowAny
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


from app.views import UserApi, SubscriberApi, ProgramApi, AuthToken


api_routes = [
    path("user/", UserApi.as_view()),
    path("subscribe/", SubscriberApi.as_view()),
    path("program/<int:program_id>", ProgramApi.as_view()),
]


SchemaView = get_schema_view(
    openapi.Info(
        title="My Health",
        default_version="v1",
        description="API to work with data from Database",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="bogdanbelenesku@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(AllowAny,),
)


urlpatterns = [
    path("", include(api_routes)),
    path("token/", AuthToken.as_view()),
    path(
        "swagger<format>/", SchemaView.without_ui(cache_timeout=0), name="schema-json"
    ),
    path(
        "swagger/",
        SchemaView.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
]
