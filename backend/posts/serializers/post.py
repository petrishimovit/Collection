from django.db import transaction
from rest_framework import serializers

from posts.models import Post, PostImage
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
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "author",
            "likes_count",
            "dislikes_count",
            "comments_count",
        )


class PostDetailSerializer(PostListSerializer):
    """
    Detailed serializer for a single post.
    Includes all basic fields and related images.
    """
    
    images = serializers.SerializerMethodField()

    class Meta(PostListSerializer.Meta):
        fields = PostListSerializer.Meta.fields + ("images",)

    def get_images(self, obj):
        """
        Return list of attached images with URL and size info.
        """
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
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = Post
        fields = ("title", "body", "images")

    def validate_images(self, files):
        # пример ограничений (можешь подправить):
        MAX_FILES = 10
        MAX_SIZE = 5 * 1024 * 1024  # 5 MB на файл
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
            PostImage.objects.bulk_create([
                PostImage(post=post, image=f) for f in images
            ])
        return post