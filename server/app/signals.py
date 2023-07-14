import os

from django.conf import settings


def remove_file(sender, instance, **kwargs):
    if not instance._state.adding:
        obj = sender.objects.get(id=instance.id)
        files = filter(lambda field: hasattr(obj, field), ["image", "video"])
        for file in files:
            rel_file_path = str(getattr(obj, file))
            abs_file_path = os.path.join(settings.MEDIA_ROOT, rel_file_path)
            if os.path.exists(abs_file_path):
                os.remove(abs_file_path)
