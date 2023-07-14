"""Import modules that work with views"""
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View

from app.forms import TelegramUserLoginForm


class AdminAuth(View):
    """
    Change admin authentication logic
    """

    def get(self, request):
        """
        GET router
        @param request:
        @return: form
        """
        form = TelegramUserLoginForm()
        return render(
            request,
            template_name="admin/login.html",
            context={"form": form, "app_path": "/admin/login"},
        )

    def post(self, request):
        """
        POST router
        @param request:
        @return: form
        """
        form = TelegramUserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect(reverse("admin:index"))
        return render(request, template_name="admin/login.html", context={"form": form})
