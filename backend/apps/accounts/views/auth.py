from django.contrib.auth import get_user_model
from rest_framework import generics, permissions

from ..serializers.user import RegisterSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    View for User Create
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer
