from rest_framework import serializers

from ..models import Item


class ItemSerializer(serializers.ModelSerializer):
    """Serializer for collection items"""

    class Meta:
        model = Item
        fields = (
            "id",
            "collection",
            "name",
            "description",
            "category",
            "is_private",
            "quantity",
            "location",
            "purchase_date",
            "purchase_price",
            "current_value",
            "currency",
            "extra",
            "images",
            "pricecharting",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "images",
            "pricecharting",
        )
