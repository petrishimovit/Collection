from rest_framework import serializers


class ReactionRequestSerializer(serializers.Serializer):
    """
    Serializer for submitting a reaction to a post or comment.
    Accepts a single field: reaction type ("like" or "dislike").
    """

    type = serializers.ChoiceField(
        choices=["like", "dislike"],
        help_text="Reaction type.",
    )
