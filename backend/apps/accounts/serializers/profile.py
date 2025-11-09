from typing import Mapping
from urllib.parse import urlparse

from rest_framework import serializers
from apps.accounts.models import Profile


from rest_framework import serializers
from apps.accounts.models import Profile

class ProfileBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("avatar", "bio", "collection_focus")
        read_only_fields = fields

class ProfileDetailSerializer(ProfileBaseSerializer):
    class Meta(ProfileBaseSerializer.Meta):
        fields = ProfileBaseSerializer.Meta.fields + ("website", "social_links")
        read_only_fields = fields

class ProfileWriteSerializer(serializers.ModelSerializer):

    avatar = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Profile
        fields = ("avatar", "bio", "collection_focus", "website", "social_links")

    def update(self, instance: Profile, validated_data):
        
        avatar = validated_data.pop("avatar", None)
        if avatar is None:
            
            avatar = self.context.get("avatar_file")

        for field, value in validated_data.items():
            setattr(instance, field, value)

        if avatar is not None:
            instance.avatar = avatar

        instance.save()
        return instance