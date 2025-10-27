from rest_framework.permissions import BasePermission


class IsProfileOwner(BasePermission):
    """Allow updates only for the owner of the profile."""
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and obj.user_id == request.user.id
