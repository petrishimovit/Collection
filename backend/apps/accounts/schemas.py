from rest_framework import serializers

from apps.accounts.serializers.profile import ProfileBaseSerializer, ProfileWriteSerializer


class FollowActionOut(serializers.Serializer):
    """
    Output schema for follow/unfollow actions.
    """

    status = serializers.ChoiceField(
        choices=["followed", "unfollowed", "not_following", "already_following"]
    )


class ProfileOut(serializers.Serializer):
    """
    Output schema for profile
    """

    display_name = serializers.CharField()
    profile = ProfileBaseSerializer()


class ProfileUpdateIn(serializers.Serializer):
    """
    Input schema for profile update
    """

    display_name = serializers.CharField(required=False, allow_blank=True)
    profile = ProfileWriteSerializer()
