from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsSelfOrStaff(BasePermission):
    """
    Permission that allows access only to:
      • the object owner (user == target_user)
      • staff users
      • superusers (implicitly allowed via is_staff or explicit check)
    """

    def has_object_permission(self, request, view, obj):
        """
        Check object-level access permissions.
        """
        user = request.user

        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True

        if hasattr(obj, "user_id"):
            target_user_id = obj.user_id
        elif hasattr(obj, "id"):
            target_user_id = obj.id
        else:
            return False

   
        if request.method in SAFE_METHODS:
            return user.id == target_user_id or user.is_staff
        return user.id == target_user_id or user.is_staff