from rest_framework import serializers
from apps.collection.models import Item


class ItemSerializer(serializers.ModelSerializer):
    """Serializer for Collection`s items"""

    items_count = serializers.IntegerField(read_only=True) # items count for pagination

    class Meta:
        model = Item
        fields = (
            "id",
            "name",
            "description",
            "purchase_date",
            "purchase_price",
            "current_value",
            "extra",
            "items_count",
            "images",
            "collection",
            "pricecharting"
            
           
        )
        read_only_fields = ("id", "created_at", "updated_at","items_count","images","pricecharting")
