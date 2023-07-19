"""Import modules for connecting signals and defining app config"""
from django.apps import AppConfig
from django.db.models.signals import pre_delete, pre_save, post_save

from django.conf import settings


class AppConfig(AppConfig):  # pylint: disable=function-redefined
    """
    App config
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "app"

    def ready(self):
        from app import signals  # pylint: disable=import-outside-toplevel
        from app.models import (  # pylint: disable=import-outside-toplevel
            TrainingProgram,
            Exercise,
        )

        post_save.connect(signals.create_auth_token, sender=settings.AUTH_USER_MODEL)

        for model in [TrainingProgram, Exercise]:
            pre_delete.connect(signals.remove_file, sender=model)
            pre_save.connect(signals.remove_file, sender=model)
