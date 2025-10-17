from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    GET - AllowAny
    POST/PUT/PATCH/DELETE - Auth & owner 
    """
    owner_attr = "owner"

    def has_permission(self, request, view):
        
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        owner = getattr(obj, getattr(self, "owner_attr", "owner"), None)
        return owner is not None and owner == request.user
