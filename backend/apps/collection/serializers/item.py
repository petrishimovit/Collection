from typing import Any, Mapping

from django.db import transaction
from rest_framework import serializers

from apps.collection.models import Collection, Item, ItemImage

from .mixins import HiddenFieldsMixin


class ItemSerializer(HiddenFieldsMixin, serializers.ModelSerializer):
    """Serializer for collection items."""

    owner_path = "collection.owner"

    images = serializers.SerializerMethodField(read_only=True)

    images_files = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        allow_empty=True,
        write_only=True,
    )

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
            "images",
            "images_files",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "pricecharting",
            "images",
        )

    def get_images(self, obj: Item):
        return [
            {
                "id": img.id,
                "url": img.image.url if img.image else None,
                "preview_sm": img.preview_sm.url if img.preview_sm else None,
                "preview_md": img.preview_md.url if img.preview_md else None,
                "order": img.order,
            }
            for img in obj.images.all().order_by("order", "created_at")
        ]

    def validate_images_files(self, files):
        max_files = 20
        max_size = 8 * 1024 * 1024

        if len(files) > max_files:
            raise serializers.ValidationError(f"Max {max_files} images.")

        for f in files:
            if getattr(f, "size", 0) > max_size:
                raise serializers.ValidationError(f"{f.name}: file size more than 8 mb")
            content_type = getattr(f, "content_type", "") or ""
            if not content_type.startswith("image/"):
                raise serializers.ValidationError(f"{f.name}: is not image")

        return files

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

    @transaction.atomic
    def create(self, validated_data: Mapping[str, Any]):
        images_files = validated_data.pop("images_files", [])
        item = Item.objects.create(**validated_data)

        for idx, f in enumerate(images_files):
            ItemImage.objects.create(item=item, image=f, order=idx)

        return item

    @transaction.atomic
    def update(self, instance: Item, validated_data: Mapping[str, Any]):
        images_files = validated_data.pop("images_files", None)

        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        if images_files is not None:
            start = instance.images.aggregate(m=models.Max("order")).get("m")
            start = (start + 1) if start is not None else 0

            for i, f in enumerate(images_files):
                ItemImage.objects.create(item=instance, image=f, order=start + i)

        return instance
