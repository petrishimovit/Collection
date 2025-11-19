from django.db.models import Count, Q, Max
from rest_framework import viewsets, permissions, response, status, decorators
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema

from apps.posts.models import Post, PostReaction
from apps.posts.permissions import IsAuthorOrReadOnly
from apps.posts.pagination import PostPagination, CommentPagination
from apps.posts.serializers import (
    PostListSerializer, PostDetailSerializer, CommentSerializer,
    ReactionRequestSerializer, PostCreateSerializer
)
from apps.posts.services.post import PostService
from apps.posts.selectors.user import following_qs 
from apps.posts.selectors.post import comments_qs


class PostViewSet(viewsets.ModelViewSet):


    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = PostPagination
    parser_classes=[MultiPartParser, FormParser, JSONParser]

    def _base_qs(self):
        return (
            Post.objects
            .select_related("author")
            .annotate(
                _likes_count=Count("reactions", filter=Q(reactions__type=PostReaction.LIKE)),
                _dislikes_count=Count("reactions", filter=Q(reactions__type=PostReaction.DISLIKE)),
                _comments_count=Count("comments"),
            )
        )

    def get_queryset(self):
        return self._base_qs().order_by("-created_at", "-id")

    def get_serializer_class(self):
        """Pick serializer by action."""
        if self.action == "create":
            return PostCreateSerializer
        return PostListSerializer if self.action == "list" else PostDetailSerializer
    
    def retrieve(self, request, *args, **kwargs):
        post = self.get_object()

        updated = PostService.register_view_for_request(
            post=post,
            user=request.user,
            request=request,
        )
        if updated:
            post.views_count = (post.views_count or 0) + 1

        serializer = self.get_serializer(post)
        return response.Response(serializer.data)

    @extend_schema(
        summary="Create a post",
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
        methods=["get", "post"],
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
            qs = comments_qs(post)
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
                post=post,
                user=request.user,
                text=ser.validated_data["text"],
            )
            out = CommentSerializer(comment, context={"request": request})
            return response.Response(out.data, status=status.HTTP_201_CREATED)


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
    
   
    @decorators.action(
        detail=False,
        methods=["get"],
        url_path="me/liked",
        permission_classes=[permissions.IsAuthenticated],
        pagination_class=PostPagination,
    )
    def liked_by_me(self, request):
       
        qs = self._base_qs().filter(
            reactions__user=request.user,
            reactions__type=PostReaction.LIKE,
        ).annotate(
            reacted_at=Max("reactions__created_at", filter=Q(reactions__user=request.user,
                                                             reactions__type=PostReaction.LIKE))
        ).order_by("-reacted_at", "-created_at", "-id").distinct()

        page = self.paginate_queryset(qs)
        ser = PostListSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(ser.data)


    @decorators.action(
        detail=False,
        methods=["get"],
        url_path="feed",
        permission_classes=[permissions.IsAuthenticated],
        pagination_class=PostPagination,
    )
    def feed(self, request):
       
        followed_users = following_qs(request.user).values("id")  
        qs = self._base_qs().filter(author_id__in=followed_users).order_by("-created_at", "-id")

        page = self.paginate_queryset(qs)
        ser = PostListSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(ser.data)
