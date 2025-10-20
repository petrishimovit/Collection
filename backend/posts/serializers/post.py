from rest_framework import serializers
from models import Post


class PostSerializer(serializers.ModelSerializer):
    """Serializer for Post"""

    items_count = serializers.IntegerField(read_only=True) 

    class Meta:
        model = Post
        fields = (
            "id", 
            "created_at", 
            "updated_at",
            "author",
            "title",
            "body"
        )
        read_only_fields = ("id", "created_at", "updated_at")