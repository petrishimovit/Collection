from rest_framework import serializers

from apps.posts.models import Comment

from .author import AuthorMiniSerializer


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for comments displayed under a post.
    Counts are read-only and come from annotations or properties.
    """

    author = AuthorMiniSerializer(read_only=True)
    likes_count = serializers.IntegerField(read_only=True, source="_likes_count")
    dislikes_count = serializers.IntegerField(read_only=True, source="_dislikes_count")

    class Meta:
        model = Comment
        fields = (
            "id",
            "created_at",
            "updated_at",
            "author",
            "text",
            "likes_count",
            "dislikes_count",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "author",
            "likes_count",
            "dislikes_count",
        )
