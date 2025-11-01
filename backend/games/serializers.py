from rest_framework import serializers
from django.shortcuts import get_object_or_404
from .models import PriceChartingConnect
from collection.models import Item
from .services.pricecharting import PricechartingService

class GameItemSerializer(serializers.Serializer):
    Game = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    GameLink = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    Year = serializers.IntegerField(required=False, allow_null=True)
    Dev = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    DevLink = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    Publisher = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    PublisherLink = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    Platform = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    PlatformLink = serializers.CharField(required=False, allow_blank=True, allow_null=True)



class SearchQuerySerializer(serializers.Serializer):
    q = serializers.CharField(max_length=200)
    region = serializers.ChoiceField(
        choices=["all", "japan", "ntsc", "pal"],
        required=False,
        default="all",
    )
    limit = serializers.IntegerField(required=False, min_value=1, max_value=50, default=10)


class ItemQuerySerializer(serializers.Serializer):
    url = serializers.URLField(required=False)
    slug = serializers.CharField(required=False)

    def validate(self, data):
        if not data.get("url") and not data.get("slug"):
            raise serializers.ValidationError("Provide `url` or `slug`.")
        return data
    



class PriceChartingConnectSerializer(serializers.ModelSerializer):
    items_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = PriceChartingConnect
        fields = (
            "id", "url", "current", "history",
            "last_synced_at", "created_at", "updated_at", "items_count"
        )


class BindSerializer(serializers.Serializer):
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
