from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsSelfOrStaff(BasePermission):
    
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        target_user_id = getattr(obj, "id", None) or getattr(obj, "user_id", None)
        return request.user.is_staff or request.user.id == target_user_id
