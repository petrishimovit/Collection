from django.db.models import Count, Q
from rest_framework import viewsets, permissions, response, status, decorators
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema

from posts.models import Post, PostReaction
from posts.permissions import IsAuthorOrReadOnly
from posts.pagination import PostPagination, CommentPagination
from posts.serializers import (
    PostListSerializer, PostDetailSerializer, CommentSerializer,
    ReactionRequestSerializer, PostCreateSerializer
)
from posts.services.post import PostService


class PostViewSet(viewsets.ModelViewSet):
    """CRUD for posts with comments and reactions."""

    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = PostPagination
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        """Base queryset with reaction and comment counters."""
        return (
            Post.objects
            .select_related("author")
            .annotate(
                _likes_count=Count("reactions", filter=Q(reactions__type=PostReaction.LIKE)),
                _dislikes_count=Count("reactions", filter=Q(reactions__type=PostReaction.DISLIKE)),
                _comments_count=Count("comments"),
            )
            .order_by("-created_at", "-id")
        )

    def get_serializer_class(self):
        """Pick serializer by action."""
        if self.action == "create":
            return PostCreateSerializer
        return PostListSerializer if self.action == "list" else PostDetailSerializer

    @extend_schema(
        summary="Create a post",
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                    "images": {"type": "array", "items": {"type": "string", "format": "binary"}},
                },
                "required": ["title"],
            }
        },
        responses={201: PostDetailSerializer},
    )
    def create(self, request, *args, **kwargs):
        """Create a post (images only on create)."""
        if not request.user.is_authenticated:
            raise PermissionDenied("Authentication required.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = serializer.save(author=request.user)
        out = PostDetailSerializer(post, context={"request": request})
        return response.Response(out.data, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        """Update a post (no images)."""
        obj = self.get_object()
        if obj.author_id != self.request.user.id:
            raise PermissionDenied("You can update only your own posts.")
        has_files = bool(getattr(self.request, "FILES", None)) and self.request.FILES
        if has_files or any(k in self.request.data for k in ("images", "alt", "order")):
            raise ValidationError("Images can only be attached when creating a post.")
        serializer.save()

    def perform_destroy(self, instance):
        """Delete a post (author only)."""
        if instance.author_id != self.request.user.id:
            raise PermissionDenied("You can delete only your own posts.")
        instance.delete()

    @decorators.action(
        detail=True,
        methods=["get", "post", "delete"],
        url_path="comments",
        pagination_class=CommentPagination,
        permission_classes=[permissions.IsAuthenticatedOrReadOnly],
    )
    @extend_schema(
        summary="Manage post comments",
        request={"POST": CommentSerializer},
        responses={200: CommentSerializer, 201: CommentSerializer, 204: None},
    )
    def comments(self, request, pk=None):
        """List, create, or delete a comment for a post."""
        post = self.get_object()

        if request.method == "GET":
            qs = PostService.comments_qs(post)
            page = self.paginate_queryset(qs)
            if page is not None:
                ser = CommentSerializer(page, many=True, context={"request": request})
                return self.get_paginated_response(ser.data)
            ser = CommentSerializer(qs, many=True, context={"request": request})
            return response.Response(ser.data)

        if request.method == "POST":
            ser = CommentSerializer(data=request.data, context={"request": request})
            ser.is_valid(raise_exception=True)
            comment = PostService.create_comment(
                post=post, user=request.user, body=ser.validated_data["body"]
            )
            out = CommentSerializer(comment, context={"request": request})
            return response.Response(out.data, status=status.HTTP_201_CREATED)

        # DELETE
        comment_id = request.query_params.get("id")
        PostService.delete_comment(post=post, user=request.user, comment_id=comment_id)
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="Toggle post reaction",
        request=ReactionRequestSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["added", "removed", "changed"]},
                    "likes": {"type": "integer"},
                    "dislikes": {"type": "integer"},
                },
                "required": ["status", "likes", "dislikes"],
            }
        },
    )
    @decorators.action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def react(self, request, pk=None):
        """Toggle like/dislike on a post."""
        post = self.get_object()
        reaction_type = request.data.get("type")
        data = PostService.toggle_reaction(post=post, user=request.user, reaction_type=reaction_type)
        return response.Response(data, status=status.HTTP_200_OK)
