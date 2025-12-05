from django.db import IntegrityError, transaction
from rest_framework import serializers

from apps.collection.models import Favorite, Item, Collection


class FavoriteSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and managing user favorites
    """

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
        model = Favorite
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

        item = (
            attrs.get("item")
            if "item" in attrs
            else getattr(self.instance, "item", None)
        )
        collection = (
            attrs.get("collection")
            if "collection" in attrs
            else getattr(self.instance, "collection", None)
        )
        title = (
            attrs.get("title")
            if "title" in attrs
            else getattr(self.instance, "title", None)
        )

  
        if kind is None:
            raise serializers.ValidationError({"kind": "This field is required."})

        if kind == Favorite.FavoriteKind.ITEM:
            if not item:
                raise serializers.ValidationError(
                    {"item_id": "item_id is required when kind='item'."}
                )
            if collection is not None:
                raise serializers.ValidationError(
                    {"collection_id": "collection_id must be null when kind='item'."}
                )

        elif kind == Favorite.FavoriteKind.COLLECTION:
            if not collection:
                raise serializers.ValidationError(
                    {"collection_id": "collection_id is required when kind='collection'."}
                )
            if item is not None:
                raise serializers.ValidationError(
                    {"item_id": "item_id must be null when kind='collection'."}
                )

        elif kind == Favorite.FavoriteKind.CUSTOM:
            if not title:
                raise serializers.ValidationError(
                    {"title": "title is required when kind='custom'."}
                )
            if item is not None or collection is not None:
                raise serializers.ValidationError(
                    "item_id and collection_id must be null when kind='custom'."
                )

        else:
            raise serializers.ValidationError({"kind": "Invalid kind value."})

       
        if user and user.is_authenticated:

         
            if kind == Favorite.FavoriteKind.ITEM and item is not None:
                owner_id = None

               
                if hasattr(item, "owner_id"):
                    owner_id = item.owner_id

                
                if owner_id is None and hasattr(item, "collection"):
                    owner_id = getattr(item.collection, "owner_id", None)

                if owner_id == user.id:
                    raise serializers.ValidationError(
                        {"item_id": "You cannot favorite your own item."}
                    )

            if (
                kind == Favorite.FavoriteKind.COLLECTION
                and collection is not None
                and collection.owner_id == user.id
            ):
                raise serializers.ValidationError(
                    {"collection_id": "You cannot favorite your own collection."}
                )

        return attrs

    def create(self, validated_data):
        """
        Create a new favorite and attach the authenticated user.
        """
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication required.")

        validated_data["user"] = user

        item = validated_data.get("item")
        collection = validated_data.get("collection")

    
        if not validated_data.get("title"):
            if item is not None:
                validated_data["title"] = item.name
            elif collection is not None:
                validated_data["title"] = collection.name

        try:
            with transaction.atomic():
                return Favorite.objects.create(**validated_data)
        except IntegrityError:
            raise serializers.ValidationError(
                "This object is already in favorites."
            )
