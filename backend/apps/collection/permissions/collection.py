from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS


class IsCollectionOwnerOrReadOnly(permissions.BasePermission):
    """
    Read:
        Always allowed (actual object visibility handled by selectors).
    Write:
        Only owner can create/update/delete.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.owner == request.user
