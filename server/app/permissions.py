from django.contrib.auth.models import Group, Permission
from rest_framework.permissions import BasePermission


class GroupPermission(BasePermission, type):
    """
    Restrict access to a view based on the user's group permissions.
    """

    def __new__(cls, **kwargs):
        for attribute_name in dir(BasePermission):
            if not attribute_name.startswith("__"):
                kwargs[attribute_name] = getattr(BasePermission, attribute_name)
        kwargs["has_permission"] = cls.has_permission
        return super(GroupPermission, cls).__new__(cls, cls.__name__, (), kwargs)

    def __init__(cls, groups=None):
        if groups is not None:
            cls.groups = Group.objects.filter(name__in=groups)
        else:
            cls.groups = []
        super(GroupPermission, cls).__init__(cls)

    def has_permission(self, request, view):
        user = request.user
        if not any(group in self.groups for group in user.groups.all()):
            return False
        return True


class UnauthenticatedPost(BasePermission):
    def has_permission(self, request, view):
        return request.method in ['POST']


class UnauthenticatedGet(BasePermission):
    def has_permission(self, request, view):
        return request.method in ['GET']


class SubscribePermission(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, "subscriber")
