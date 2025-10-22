from django.db.models import Count, Q
from rest_framework import viewsets, permissions, response, status, decorators
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema, OpenApiRequest

from posts.models import Post, Comment
from posts.permissions import IsAuthorOrReadOnly
from posts.pagination import PostPagination, CommentPagination
from posts.serializers import PostListSerializer, PostDetailSerializer, CommentSerializer
from posts.serializers import PostCreateSerializer


class PostViewSet(viewsets.ModelViewSet):
    """
    **Posts:**

    - **GET /api/posts/** — Paginated list of posts  
    - **POST /api/posts/** — Create a new post *(authenticated, images allowed only here)*  
    - **GET /api/posts/{id}/** — Retrieve a single post  
    - **PATCH /api/posts/{id}/** — Partially update a post *(author only, no images)*  
    - **PUT /api/posts/{id}/** — Fully update a post *(author only, no images)*  
    - **DELETE /api/posts/{id}/** — Delete a post *(author only)*  

    **Comments:**

    - **GET /api/posts/{id}/comments/** — Paginated list of comments for the post  
    - **POST /api/posts/{id}/comments/** — Create a new comment *(authenticated)*
    """
    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = PostPagination
    parser_classes = [JSONParser, MultiPartParser, FormParser]  

    def get_queryset(self):
        return (
            Post.objects
            .select_related("author")
            .annotate(
                _likes_count=Count("reactions", filter=Q(reactions__type="like")),
                _dislikes_count=Count("reactions", filter=Q(reactions__type="dislike")),
                _comments_count=Count("comments"),
            )
            .order_by("-created_at", "-id")
        )

    def get_serializer_class(self):
       
        if self.action == "create":
            return PostCreateSerializer
        return PostListSerializer if self.action == "list" else PostDetailSerializer

    @extend_schema(
    request={
        "multipart/form-data": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "body": {"type": "string"},
                "images": {
                    "type": "array",
                    "items": {"type": "string", "format": "binary"},
                },
            },
            "required": ["title"],
        }
    },
    responses={201: PostDetailSerializer},
   )
    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("Authentication required.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        post = serializer.save(author=request.user)
        
        out = PostDetailSerializer(post, context={"request": request})
        return response.Response(out.data, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        obj = self.get_object()
        if obj.author_id != self.request.user.id:
            raise PermissionDenied("You can update only your posts.")
        # forbid passing images in update
        has_files = bool(getattr(self.request, "FILES", None)) and self.request.FILES
        if has_files or any(k in self.request.data for k in ("images", "alt", "order")):
            raise ValidationError("Images can only be attached when creating a post.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.author_id != self.request.user.id:
            raise PermissionDenied("You can delete only your posts.")
        instance.delete()

   
    @decorators.action(
    detail=True,
    methods=["get", "post", "delete"],
    url_path="comments",
    pagination_class=CommentPagination,
    permission_classes=[permissions.IsAuthenticatedOrReadOnly],
)
    def comments(self, request, pk=None):
        post = self.get_object()

        if request.method == "GET":
            qs = (
            Comment.objects
            .filter(post=post)
            .select_related("author")
            .annotate(
                _likes_count=Count("reactions", filter=Q(reactions__type="like")),
                _dislikes_count=Count("reactions", filter=Q(reactions__type="dislike")),
            )
            .order_by("created_at", "id")
        )
            page = self.paginate_queryset(qs)
            if page is not None:
                ser = CommentSerializer(page, many=True, context={"request": request})
                return self.get_paginated_response(ser.data)
        ser = CommentSerializer(qs, many=True, context={"request": request})
        return response.Response(ser.data)

  
        if request.method == "POST":
            if not request.user.is_authenticated:
                raise PermissionDenied("Authentication required.")
            ser = CommentSerializer(data=request.data, context={"request": request})
            ser.is_valid(raise_exception=True)
            comment = Comment.objects.create(
            post=post,
            author=request.user,
            body=ser.validated_data["body"],
        )
            out = CommentSerializer(comment, context={"request": request})
            return response.Response(out.data, status=status.HTTP_201_CREATED)

 
        if request.method == "DELETE":
            if not request.user.is_authenticated:
                raise PermissionDenied("Authentication required.")
            comment_id = request.query_params.get("id")
            if not comment_id:
                raise ValidationError("Missing ?id= parameter for comment deletion.")

            try:
                comment = Comment.objects.get(id=comment_id, post=post)
            except Comment.DoesNotExist:
                raise ValidationError("Comment not found.")

            if comment.author_id != request.user.id:
                raise PermissionDenied("You can delete only your own comments.")

            comment.delete()
            return response.Response(status=status.HTTP_204_NO_CONTENT)
