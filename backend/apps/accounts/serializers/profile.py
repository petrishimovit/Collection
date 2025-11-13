from typing import Mapping
from rest_framework import serializers
from apps.accounts.models import Profile


class ProfileBaseSerializer(serializers.ModelSerializer):
    """
    Base read-only profile serializer.
    """

    class Meta:
        model = Profile
        fields = ("avatar", "bio", "collection_focus")
        read_only_fields = fields


class ProfileDetailSerializer(ProfileBaseSerializer):
    """
    Detailed read-only profile serializer.
    Includes website and social links.
    """

    class Meta(ProfileBaseSerializer.Meta):
        fields = ProfileBaseSerializer.Meta.fields + ("website", "social_links")
        read_only_fields = fields


class ProfileWriteSerializer(serializers.ModelSerializer):
    """
    Serializer for updating profile data.
    """

    avatar = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Profile
        fields = ("avatar", "bio", "collection_focus", "website", "social_links")

    def update(self, instance: Profile, validated_data: Mapping):
        """
        Update profile fields and handle avatar upload.
        """
        avatar = validated_data.pop("avatar", None)
        if avatar is None:
            avatar = self.context.get("avatar_file")

        for field, value in validated_data.items():
            setattr(instance, field, value)

        if avatar is not None:
            instance.avatar = avatar

        instance.save()
        return instance
