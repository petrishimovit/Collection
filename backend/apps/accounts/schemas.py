from rest_framework import serializers
from apps.accounts.serializers.profile import ProfileBaseSerializer, ProfileWriteSerializer

class FollowActionOut(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=["followed", "unfollowed", "not_following", "already_following"]
    )

class ProfileOut(serializers.Serializer):
    display_name = serializers.CharField()
    profile = ProfileBaseSerializer()

class ProfileUpdateIn(serializers.Serializer):
    display_name = serializers.CharField(required=False, allow_blank=True)
    profile = ProfileWriteSerializer()
