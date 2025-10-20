from rest_framework import serializers
from models import Comment


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for Post"""

    items_count = serializers.IntegerField(read_only=True) 

    class Meta:
        model = Comment
        fields = (
            "id", 
            "created_at", 
            "updated_at",
            "author",
            "title",
            "body"
        )
        read_only_fields = ("id", "created_at", "updated_at")
