from rest_framework import permissions, generics
from django.contrib.auth import get_user_model
from ..serializers.user import RegisterSerializer

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

