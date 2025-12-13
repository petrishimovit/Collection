from rest_framework import viewsets, permissions, response, status, decorators,serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.filters import OrderingFilter
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    inline_serializer,
)

from drf_spectacular.types import OpenApiTypes

from apps.posts.models import PostReaction
from apps.posts.permissions import IsAuthorOrReadOnly
from apps.posts.pagination import PostPagination, CommentPagination
from apps.posts.serializers import (
    PostListSerializer,
    PostDetailSerializer,
    CommentSerializer,
    ReactionRequestSerializer,
    PostCreateSerializer,
)
from apps.posts.services.post import PostService
from apps.posts.selectors.post import (
    comments_qs,
    posts_list_qs,
    liked_by_user_qs,
    feed_qs,
    search_posts_qs,
)

from apps.notifications.services import NotificationService


@extend_schema_view(
    list=extend_schema(
        summary="List posts",
        description="Return a paginated list of posts ordered by creation date.",
        responses={200: PostListSerializer},
        tags=["Posts"],
        parameters=[
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description=(
                    "Sort posts by one of: "
                    "`created_at`, `-created_at`, "
                    "`views_count`, `-views_count`, "
                    "`likes_count`, `-likes_count`."
                ),
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Retrieve a post",
        description="Return a single post by ID.",
        responses={200: PostDetailSerializer},
        tags=["Posts"],
    ),
    create = extend_schema(
    summary="Create a post",
    request=inline_serializer(
        name="PostCreateRequest",
        fields={
            "text": serializers.CharField(),
            "images": serializers.ImageField(
                required=False,
            
            ),
        },
    ),
    responses={201: PostDetailSerializer},
    tags=["Posts"],
),
    destroy=extend_schema(
        summary="Delete a post",
        description="Soft delete a post created by the authenticated user.",
        tags=["Posts"],
    ),
)
class PostViewSet(viewsets.ModelViewSet):
    """
    Post CRUD and extra actions:
    - comments list/create
    - like/dislike reactions
    - liked-by-me list
    - personalized feed
    - search
    """

    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = PostPagination
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    http_method_names = ["get", "post", "delete", "head", "options"]

    filter_backends = (OrderingFilter,)
    ordering_fields = (
        "created_at",
        "views_count",
        "likes_count",
    )
    ordering = ("-created_at",)

    def get_queryset(self):
        """Return default posts list queryset."""
        return posts_list_qs()

    def get_serializer_class(self):
        """Return serializer based on action."""
        if self.action == "create":
            return PostCreateSerializer
        return PostListSerializer if self.action == "list" else PostDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        """Retrieve and register a view for the post."""
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

    def create(self, request, *args, **kwargs):
        """Create a new post (images allowed only during creation)."""
        if not request.user.is_authenticated:
            raise PermissionDenied("Authentication required.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = serializer.save(author=request.user)
        NotificationService().create_post_for_followers(author=request.user, post=post)
        out = PostDetailSerializer(post, context={"request": request})
        return response.Response(out.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        """Soft delete a post (author only)."""
        if instance.author_id != self.request.user.id:
            raise PermissionDenied("You can delete only your own posts.")

        if getattr(instance, "is_deleted", False):
            raise ValidationError("Post is already deleted.")

        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])

    @extend_schema(
        summary="List or create comments",
        description="GET: list comments for a post. POST: create a new comment.",
        request=CommentSerializer,
        responses={200: CommentSerializer(many=True), 201: CommentSerializer},
        tags=["Posts"],
        
    )
    @decorators.action(
        detail=True,
        methods=["get", "post"],
        url_path="comments",
        pagination_class=CommentPagination,
        permission_classes=[permissions.IsAuthenticatedOrReadOnly],
        filter_backends=[], 
    )
    def comments(self, request, pk=None):
        """List or create comments for the post."""
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
        description="Toggle like or dislike on a post. Returns updated counters.",
        request=ReactionRequestSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["added", "removed", "changed"]},
                    "likes": {"type": "integer"},
                    "dislikes": {"type": "integer"},
                },
            }
        },
        tags=["Posts"],
    )
    @decorators.action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def react(self, request, pk=None):
        """Toggle like or dislike on a post."""
        post = self.get_object()
        reaction_type = request.data.get("type")

        data = PostService.toggle_reaction(
            post=post,
            user=request.user,
            reaction_type=reaction_type,
        )

        is_added = False
        if isinstance(data, dict):
            if data.get("active") is True:
                is_added = True
            if data.get("status") in {"added", "created", "on", "liked", "disliked"}:
                is_added = True

        if is_added:
            NotificationService().create_post_reaction(
                post=post,
                actor=request.user,
                reaction_type=str(reaction_type),
            )

        return response.Response(data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="List posts liked by me",
        description="Return posts liked by the authenticated user, ordered by latest reaction.",
        responses={200: PostListSerializer},
        tags=["Posts"],
    )
    @decorators.action(
        detail=False,
        methods=["get"],
        url_path="me/liked",
        permission_classes=[permissions.IsAuthenticated],
        pagination_class=PostPagination,
    )
    def liked_by_me(self, request):
        """Return posts liked by the authenticated user."""
        qs = liked_by_user_qs(request.user)
        page = self.paginate_queryset(qs)
        ser = PostListSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(ser.data)

    @extend_schema(
        summary="Personalized feed",
        description="Return a feed of posts from authors the user follows, ordered by recency and activity.",
        responses=PostListSerializer(many=True),
        tags=["Posts"],
        parameters=[
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description=(
                    "Sort feed by one of: "
                    "`created_at`, `-created_at`, "
                    "`views_count`, `-views_count`, "
                    "`likes_count`, `-likes_count`."
                ),
            ),
        ],
    )
    @decorators.action(
        detail=False,
        methods=["get"],
        url_path="feed",
        permission_classes=[permissions.IsAuthenticated],
        pagination_class=PostPagination,
    )
    def feed(self, request):
        """Return personalized feed from followed authors."""
        qs = feed_qs(request.user)
        qs = self.filter_queryset(qs)
        page = self.paginate_queryset(qs)
        ser = PostListSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(ser.data)

    @extend_schema(
        summary="Search posts",
        description="Search posts by text content using a simple case-insensitive match.",
        parameters=[
            OpenApiParameter(
                name="q",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Search query string.",
            ),
        ],
        responses=PostListSerializer(many=True),
        tags=["Posts"],
    )
    @decorators.action(
        detail=False,
        methods=["get"],
        url_path="search",
        pagination_class=PostPagination,
        permission_classes=[permissions.AllowAny],
    )
    def search(self, request):
        """Search posts by a query string in the text field."""
        query = request.query_params.get("q", "").strip()
        if not query:
            raise ValidationError({"q": "Query parameter 'q' is required."})

        qs = search_posts_qs(query)
        page = self.paginate_queryset(qs)
        ser = PostListSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(ser.data)
