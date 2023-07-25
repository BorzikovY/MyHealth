"""Imports that work with urls"""
from django.urls import path, include
from drf_yasg.generators import OpenAPISchemaGenerator
from rest_framework.permissions import AllowAny
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from app.views import (
    AuthToken,
    UserApi,
    SubscriberApi,
    ProgramApi,
    NutritionApi,
    TrainingApi,
    ExerciseApi,
    ProgramListApi,
    NutritionListApi,
    TrainingListApi,
    ExerciseListApi
)

api_routes = [
    path("user/", UserApi.as_view(), name="user"),
    path("subscribe/", SubscriberApi.as_view(), name="subscribe"),
    path("program/<int:program_id>", ProgramApi.as_view(), name="program"),
    path("nutrition/<int:nutrition_id>", NutritionApi.as_view(), name="nutrition"),
    path("training/<int:training_id>", TrainingApi.as_view(), name="training"),
    path("exercise/<int:exercise_id>", ExerciseApi.as_view(), name="exercise"),
    path("program/list", ProgramListApi.as_view({'get': 'list'})),
    path("nutrition/list", NutritionListApi.as_view({'get': 'list'})),
    path("training/list", TrainingListApi.as_view({'get': 'list'})),
    path("exercise/list", ExerciseListApi.as_view({'get': 'list'}))
]


class SchemaGenerator(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        schema = super(SchemaGenerator, self).get_schema(request, public)
        schema.schemes = ["http", "https"]

        return schema


SchemaView = get_schema_view(
    openapi.Info(
        title="My Health",
        default_version="v1",
        description="API to work with data from Database",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="bogdanbelenesku@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    generator_class=SchemaGenerator,
    public=True,
    permission_classes=(AllowAny,),
)


urlpatterns = [
    path("", include(api_routes)),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain"),
    path("token/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "swagger<format>/", SchemaView.without_ui(cache_timeout=0), name="schema-json"
    ),
    path(
        "swagger/",
        SchemaView.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
]
