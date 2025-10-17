from rest_framework import serializers
from collection.models import Collection


class CollectionSerializer(serializers.ModelSerializer):
    """Serializer for Collection"""

    items_count = serializers.IntegerField(read_only=True) # items count for pagination

    class Meta:
        model = Collection
        fields = (
            "id",
            "name",
            "image",
            "items_count",
            "created_at",
            "updated_at",
            "owner",
            "items"
           
        )
        read_only_fields = ("id", "created_at", "updated_at","owner","image","items")
