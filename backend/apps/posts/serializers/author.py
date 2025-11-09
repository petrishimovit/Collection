from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

class AuthorMiniSerializer(serializers.ModelSerializer):
    """
    Minimal author representation intended for nested usage.
    """
    class Meta:
        model = User
        fields = ("id", "display_name")
