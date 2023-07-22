"""Imports that work with permissions"""
from django.contrib.auth.models import Group
from rest_framework.permissions import BasePermission


class GroupPermission(BasePermission, type):
    """
    Restrict access to a view based on the user's group permissions.
    """

    def __new__(cls, **kwargs):  # pylint: disable=bad-mcs-classmethod-argument
        for attribute_name in dir(BasePermission):
            if not attribute_name.startswith("__"):
                kwargs[attribute_name] = getattr(BasePermission, attribute_name)

        kwargs["has_permission"] = cls.has_permission

        return super(  # pylint: disable=redefined-outer-name
            GroupPermission, cls
        ).__new__(cls, cls.__name__, (), kwargs)

    def __init__(cls, groups=None):
        if groups is not None:
            cls.groups = Group.objects.filter(name__in=groups)
        else:
            cls.groups = []
        super(GroupPermission, cls).__init__(cls)

    def has_permission(  # pylint: disable=bad-mcs-method-argument
        self, request, view
    ) -> bool:
        user = request.user
        if not any(group in self.groups for group in user.groups.all()):
            return False
        return True


class UnauthenticatedPost(BasePermission):
    """Permission for accessing post method to any user"""

    def has_permission(self, request, view) -> bool:
        return request.method in ["POST"]


class UnauthenticatedGet(BasePermission):
    """Permission for accessing get method to any user"""

    def has_permission(self, request, view) -> bool:
        return request.method in ["GET"]


class SubscribePermission(BasePermission):
    """Permission for accessing api to subscribers (only)"""

    def has_permission(self, request, view) -> bool:
        return hasattr(request.user, "subscriber")
