
from typing import Mapping
from urllib.parse import urlparse

from rest_framework import serializers
from accounts.models import Profile


ALLOWED_SOCIAL_KEYS = {
    "youtube", "instagram", "tiktok", "x", "twitter", "vk",
    "telegram", "facebook", "twitch", "ebay", "website", "avito"
}


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
 
    class Meta:
        model = Profile
        fields = ("avatar", "bio", "collection_focus", "website", "social_links")

   
    def validate_social_links(self, value: Mapping[str, str]):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Must be an object of key->url.")

   
        if len(value) > Profile.MAX_SOCIAL_LINKS:
            raise serializers.ValidationError(f"Max {Profile.MAX_SOCIAL_LINKS} links.")

       
        unknown = [k for k in value.keys() if k not in ALLOWED_SOCIAL_KEYS]
        if unknown:
            raise serializers.ValidationError(
                f"Unsupported keys: {', '.join(unknown)}. "
                f"Allowed: {', '.join(sorted(ALLOWED_SOCIAL_KEYS))}."
            )


        for k, url in value.items():
            if not isinstance(url, str) or not url:
                raise serializers.ValidationError(f"Value for '{k}' must be a non-empty string.")
            parsed = urlparse(url)
            if not (parsed.scheme in {"http", "https"} and parsed.netloc):
                raise serializers.ValidationError(f"Invalid URL for '{k}': '{url}'.")

        return value
