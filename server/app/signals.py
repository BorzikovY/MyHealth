"""Import modules that works with files and their paths"""
import os

from django.conf import settings
from rest_framework.authtoken.models import Token


def remove_file(sender, instance, **kwargs) -> None:  # pylint: disable=unused-argument
    """
    Function which delete files when instance is updated or deleted
    @param sender: model
    @param instance:
    @param kwargs:
    @return: None
    """
    if not instance._state.adding:  # pylint: disable=protected-access
        obj = sender.objects.get(id=instance.id)
        files = filter(lambda field: hasattr(obj, field), ["image", "video"])
        for file in filter(
            lambda field: getattr(instance, field) != getattr(obj, field), files
        ):
            rel_file_path = str(getattr(obj, file))
            abs_file_path = os.path.join(settings.MEDIA_ROOT, rel_file_path)
            if os.path.exists(abs_file_path):
                os.remove(abs_file_path)
