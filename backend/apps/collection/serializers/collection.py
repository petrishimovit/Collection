from rest_framework import serializers

from ..models import Collection


class CollectionSerializer(serializers.ModelSerializer):
    """Serializer for Collection"""


    items_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Collection
        fields = (
            "id",
            "name",
            "description",
            "image",
            "privacy",
            "views_count",
            "items_count",
            "created_at",
            "updated_at",
            "owner",
            "items",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "owner",
            "views_count",
            "items_count",
            "items",
        )
