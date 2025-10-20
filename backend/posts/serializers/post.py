from rest_framework import serializers
from posts.models import Post
from .author import AuthorMiniSerializer

class PostListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing posts.
    Provides reaction counts and comments_count for list view.
    """
    author = AuthorMiniSerializer(read_only=True)
    likes_count = serializers.IntegerField(read_only=True, source="_likes_count")
    dislikes_count = serializers.IntegerField(read_only=True, source="_dislikes_count")
    comments_count = serializers.IntegerField(read_only=True, source="_comments_count")
    
    class Meta:
        model = Post
        fields = (
            "id",
            "created_at",
            "updated_at",
            "author",
            "title",
            "body",
            "likes_count",
            "dislikes_count",
            "comments_count",
        )
        read_only_fields = ("id", "created_at", "updated_at", "author", "likes_count", "dislikes_count", "comments_count")


class PostDetailSerializer(PostListSerializer):
    """
    Detailed serializer for single post view.
    Currently same as list; comments are fetched via a separate endpoint.
    """
    pass
