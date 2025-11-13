from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.posts.views.post import PostViewSet
from apps.posts.views.comment import CommentViewSet

router = DefaultRouter()
router.register(r"posts", PostViewSet, basename="post")
router.register(r"comments", CommentViewSet, basename="comment")


urlpatterns = router.urls