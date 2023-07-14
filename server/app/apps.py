from django.apps import AppConfig
from django.db.models.signals import pre_delete, pre_save


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        from app import signals
        from app.models import TrainingProgram, Exercise

        for model in [TrainingProgram, Exercise]:
            pre_delete.connect(signals.remove_file, sender=model)
            pre_save.connect(signals.remove_file, sender=model)

