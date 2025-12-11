from rest_framework import serializers

from apps.collection.models import Collection


class CollectionSerializer(serializers.ModelSerializer):
    """Serializer for collections."""

    items_count = serializers.IntegerField(read_only=True)
    total_current_value = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True,
    )
    total_purchase_price = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True,
    )

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
            "total_current_value",
            "total_purchase_price",
            "created_at",
            "updated_at",
            "owner",
            "is_favorite",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "owner",
            "views_count",
            "items_count",
            "total_current_value",
            "total_purchase_price",
            "items",
        )
