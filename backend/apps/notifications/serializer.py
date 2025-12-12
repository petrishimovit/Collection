from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Read-only notification serializer."""

    class Meta:
        model = Notification
        fields = ("id", "created_at", "type", "is_checked")
        read_only_fields = fields
