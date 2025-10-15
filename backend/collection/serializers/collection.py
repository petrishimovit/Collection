from rest_framework import serializers
from collection.models import Collection


class CollectionSerializer(serializers.ModelSerializer):
    """Basic serializer for Collection model (without nested items)."""

    items_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Collection
        fields = (
            "id",
            "name",
            "image",
            "items_count",
            "created_at",
            "updated_at",
            "owner"
        )
        read_only_fields = ("id", "created_at", "updated_at")
