from django.contrib.auth.views import LoginView
from django.urls import path, include

from rest_framework import routers

from app.forms import TelegramUserLoginForm
from app.views import TelegramUserViewSet

router = routers.DefaultRouter()
router.register("telegram_users", TelegramUserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', LoginView.as_view(
        template_name="rest/login.html",
        authentication_form=TelegramUserLoginForm
    ), name='login'),
    path('auth/', include('rest_framework.urls'))
]
