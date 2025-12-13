from rest_framework import serializers

from apps.collection.models import Collection, Item

from .mixins import HiddenFieldsMixin


class ItemSerializer(HiddenFieldsMixin, serializers.ModelSerializer):
    """Serializer for collection items."""

    owner_path = "collection.owner"

    class Meta:
        model = Item
        fields = (
            "id",
            "name",
            "description",
            "category",
            "privacy",
            "quantity",
            "location",
            "purchase_date",
            "purchase_price",
            "current_value",
            "currency",
            "extra",
            "hidden_fields",
            "collection",
            "pricecharting",
            "created_at",
            "updated_at",
            "for_sale",
            "is_favorite",
        )
        read_only_fields = ("id", "created_at", "updated_at", "pricecharting")

    def validate(self, attrs):
        """
        Ensure item privacy is not less restrictive than collection privacy.

        Rules:
            - if collection is private -> item must be private
            - if collection is following_only -> item cannot be public
        """
        collection = attrs.get("collection") or getattr(self.instance, "collection", None)
        privacy = attrs.get("privacy") or getattr(self.instance, "privacy", None)

        if collection is None or privacy is None:
            return attrs

        collection_privacy = collection.privacy

        if collection_privacy == Collection.PRIVACY_PRIVATE and privacy != Item.PRIVACY_PRIVATE:
            raise serializers.ValidationError(
                {"privacy": "Item privacy must be private when collection is private."}
            )

        if collection_privacy == Collection.PRIVACY_FOLLOWING and privacy == Item.PRIVACY_PUBLIC:
            raise serializers.ValidationError(
                {"privacy": "Item in following-only collection cannot be public."}
            )

        return attrs
