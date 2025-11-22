from django.db import transaction
from rest_framework import serializers

from apps.posts.models import Post, PostImage
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
            "text",
            "likes_count",
            "dislikes_count",
            "comments_count",
            "views_count"

        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "author",
            "likes_count",
            "dislikes_count",
            "comments_count",
            "views_count"
        )


class PostDetailSerializer(PostListSerializer):
    """
    Detailed serializer for a single post.
    Includes attached images and reaction counters.
    """

    images = serializers.SerializerMethodField()

    class Meta(PostListSerializer.Meta):
        fields = PostListSerializer.Meta.fields + (
            "images",
            "likes_count",
            "dislikes_count",
        )
        read_only_fields = PostListSerializer.Meta.read_only_fields

    def get_images(self, obj):
        return [
            {
                "id": img.id,
                "url": img.image.url,
                "width": img.width,
                "height": img.height,
            }
            for img in obj.images.all().order_by("id")
        ]



class PostCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a post with optional image uploads.
    """
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        allow_empty=True,
        write_only=True,
    )

    class Meta:
        model = Post
        fields = ("text", "images")

    def validate_images(self, files):
        """
        Validate uploaded images count, size and content type.
        """
        MAX_FILES = 10
        MAX_SIZE = 5 * 1024 * 1024  # 5 MB

        if len(files) > MAX_FILES:
            raise serializers.ValidationError(f"Максимум {MAX_FILES} изображений.")

        for f in files:
            if f.size > MAX_SIZE:
                raise serializers.ValidationError(f"{f.name}: файл больше 5MB.")
            if not f.content_type.startswith("image/"):
                raise serializers.ValidationError(f"{f.name}: не является изображением.")

        return files

    @transaction.atomic
    def create(self, validated_data):
        images = validated_data.pop("images", [])
        post = Post.objects.create(**validated_data)
        if images:
            PostImage.objects.bulk_create(
                [PostImage(post=post, image=f) for f in images]
            )
        return post