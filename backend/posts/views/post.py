from django.db.models import Count, Q
from rest_framework import viewsets, permissions, response, status, decorators
from rest_framework.exceptions import PermissionDenied

from posts.models import Post, Comment
from posts.permissions import IsAuthorOrReadOnly
from posts.pagination import PostPagination, CommentPagination
from posts.serializers import (
    PostListSerializer, PostDetailSerializer, CommentSerializer
)


class PostViewSet(viewsets.ModelViewSet):
    """
    **Posts:**

    - **GET /api/posts/** — Paginated list of posts  
    - **POST /api/posts/** — Create a new post *(authenticated)*  
    - **GET /api/posts/{id}/** — Retrieve a single post  
    - **PATCH /api/posts/{id}/** — Partially update a post *(author only)*  
    - **PUT /api/posts/{id}/** — Fully update a post *(author only)*  
    - **DELETE /api/posts/{id}/** — Delete a post *(author only)*  

    **Comments:**

    - **GET /api/posts/{id}/comments/** — Paginated list of comments for the post  
    - **POST /api/posts/{id}/comments/** — Create a new comment *(authenticated)*
    """
    
    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = PostPagination

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
        """Use compact serializer for list and detailed for retrieve/create/update."""
        return PostListSerializer if self.action == "list" else PostDetailSerializer

    def perform_create(self, serializer):
        """
        Enforce current user as the author to prevent spoofing via payload.
        """
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentication required.")
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        """
        Only the author is allowed to update the post.
        """
        obj = self.get_object()
        if obj.author_id != self.request.user.id:
            raise PermissionDenied("You can update only your posts.")
        serializer.save()

    def perform_destroy(self, instance):
        """
        Only the author is allowed to delete the post.
        """
        if instance.author_id != self.request.user.id:
            raise PermissionDenied("You can delete only your posts.")
        instance.delete()

    @decorators.action(
        detail=True,
        methods=["get", "post"],
        url_path="comments",
        pagination_class=CommentPagination,
        permission_classes=[permissions.IsAuthenticatedOrReadOnly],
    )
    def comments(self, request, pk=None):
        """
        List or create comments under the post.

        GET:
            Returns a paginated list ordered by (created_at, id).
        POST:
            Creates a new comment authored by the current user.
        """
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

        # POST
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
