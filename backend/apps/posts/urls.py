from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.posts.views.comment import CommentViewSet
from apps.posts.views.post import PostViewSet
from apps.posts.views.user import UserPostsViewSet

router = DefaultRouter()
router.register(r"posts", PostViewSet, basename="post")
router.register(r"comments", CommentViewSet, basename="comment")


urlpatterns = router.urls

urlpatterns = router.urls + [
    path(
        "users/<uuid:id>/posts/", UserPostsViewSet.as_view({"get": "list"}), name="user-posts-list"
    ),
]
