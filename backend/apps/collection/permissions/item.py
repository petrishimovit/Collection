from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS


class IsItemOwnerOrReadOnly(permissions.BasePermission):
    """
    Read:
        Always allowed (visibility handled in selectors).
    Write:
        Only owner of the item's collection.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.collection.owner == request.user
