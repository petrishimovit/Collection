from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework import serializers

from apps.collection.models import Item
from apps.games.models import PriceChartingConnect
from apps.games.services.pricecharting import PricechartingService


class SearchQuerySerializer(serializers.Serializer):
    """
    query params for priceCharting search endpoint.
    """

    q = serializers.CharField(max_length=200)
    region = serializers.ChoiceField(
        choices=["all", "japan", "ntsc", "pal"],
        required=False,
        default="all",
    )
    limit = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=50,
        default=10,
    )


class ItemQuerySerializer(serializers.Serializer):
    """
    query params for priceCharting item-details endpoint.
    """

    url = serializers.URLField(required=False)
    slug = serializers.CharField(required=False)

    def validate(self, data):
        if not data.get("url") and not data.get("slug"):
            raise serializers.ValidationError("Provide `url` or `slug`.")
        return data


class PriceChartingConnectSerializer(serializers.ModelSerializer):
    """
    public representation of priceChartingConnect model.
    """

    items_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = PriceChartingConnect
        fields = (
            "id",
            "url",
            "current",
            "history",
            "last_synced_at",
            "created_at",
            "updated_at",
            "items_count",
        )


class BindSerializer(serializers.Serializer):
    """
    bind a user collection item to a priceCharting url

    required:
        item_id — UUID of collection Item
        url     — PriceCharting link
    """

    item_id = serializers.UUIDField()
    url = serializers.URLField()

    def validate(self, attrs):
        request = self.context["request"]

        item = get_object_or_404(
            Item.objects.select_related("collection"),
            id=attrs["item_id"],
        )

        if item.collection.owner != request.user:
            raise serializers.ValidationError("You are not the owner of this item.")

        attrs["item"] = item
        return attrs

    def create(self, validated_data):
        return PricechartingService.bind_item(
            item=validated_data["item"],
            url=validated_data["url"],
        )


class UnbindSerializer(serializers.Serializer):
    """
    unbind a user collection item from priceCharting.

    required:
        item_id — UUID of collection Item

    """

    item_id = serializers.UUIDField()

    def validate(self, attrs):
        request = self.context["request"]

        item = get_object_or_404(
            Item.objects.select_related("collection"),
            id=attrs["item_id"],
        )

        if item.collection.owner != request.user:
            raise serializers.ValidationError("You are not the owner of this item.")

        attrs["item"] = item
        return attrs

    def create(self, validated_data):
        PricechartingService.unbind_item(validated_data["item"])
        return validated_data["item"]
