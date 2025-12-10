from django.db import IntegrityError, transaction
from rest_framework import serializers

from apps.collection.models import WishList, Item, Collection


class WishListSerializer(serializers.ModelSerializer):
    item_id = serializers.PrimaryKeyRelatedField(
        source="item",
        queryset=Item.objects.all(),
        required=False,
        allow_null=True,
    )

    collection_id = serializers.PrimaryKeyRelatedField(
        source="collection",
        queryset=Collection.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = WishList
        fields = (
            "id",
            "kind",
            "title",
            "item_id",
            "collection_id",
            "external_url",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        kind = attrs.get("kind") or getattr(self.instance, "kind", None)

        item = attrs.get("item") if "item" in attrs else getattr(self.instance, "item", None)
        collection = attrs.get("collection") if "collection" in attrs else getattr(self.instance, "collection", None)
        title = attrs.get("title") if "title" in attrs else getattr(self.instance, "title", None)

        if kind == WishList.Kind.ITEM:
            if not item:
                raise serializers.ValidationError({"item_id": "item_id is required when kind='item'."})
            if collection is not None:
                raise serializers.ValidationError({"collection_id": "collection_id must be null when kind='item'."})

        elif kind == WishList.Kind.COLLECTION:
            if not collection:
                raise serializers.ValidationError({"collection_id": "collection_id is required when kind='collection'."})
            if item is not None:
                raise serializers.ValidationError({"item_id": "item_id must be null when kind='collection'."})

        elif kind == WishList.Kind.CUSTOM:
            if not title:
                raise serializers.ValidationError({"title": "title is required when kind='custom'."})
            if item or collection:
                raise serializers.ValidationError("item_id and collection_id must be null when kind='custom'.")

        else:
            raise serializers.ValidationError({"kind": "Invalid kind value."})

        # Logic: forbid wishlisting own objects
        if user and user.is_authenticated:
            if kind == WishList.Kind.ITEM and item is not None:
                item_owner_id = getattr(item.collection, "owner_id", None)
                if item_owner_id == user.id:
                    raise serializers.ValidationError({"item_id": "You cannot favorite your own item."})

            if kind == WishList.Kind.COLLECTION and collection is not None:
                if collection.owner_id == user.id:
                    raise serializers.ValidationError({"collection_id": "You cannot favorite your own collection."})

        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        validated_data["user"] = user

        if not validated_data.get("title"):
            if validated_data.get("item"):
                validated_data["title"] = validated_data["item"].name
            elif validated_data.get("collection"):
                validated_data["title"] = validated_data["collection"].name

        try:
            with transaction.atomic():
                return WishList.objects.create(**validated_data)
        except IntegrityError:
            raise serializers.ValidationError("This object is already in favorites.")
