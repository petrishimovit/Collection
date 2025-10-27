from rest_framework import viewsets, permissions, response, status
from accounts.models import Profile
from accounts.serializers.profile import (
    ProfileBaseSerializer,
    ProfileDetailSerializer,
    ProfileWriteSerializer,
)
from accounts.permissions import IsProfileOwner


class ProfileViewSet(viewsets.ModelViewSet):
    """
    - /profiles/          -> list (public, lightweight)
    - /profiles/{id}/     -> retrieve (public, detailed)
    - /profiles/{id}/PATCH -> update (owner only)
    - Create/Destroy disabled (profiles are created via signal).
    """
    queryset = Profile.objects.select_related("user")
    http_method_names = ["get", "patch", "head", "options"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsProfileOwner()]

    def get_serializer_class(self):
        if self.action == "list":
            return ProfileBaseSerializer
        if self.action == "retrieve":
            return ProfileDetailSerializer
        return ProfileWriteSerializer  # for PATCH
