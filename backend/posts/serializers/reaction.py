from rest_framework import serializers

class ReactionRequestSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["like", "dislike"])