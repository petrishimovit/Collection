from django.urls import path, include
from rest_framework.routers import DefaultRouter
from posts.views.post import PostViewSet
from posts.views.comment import CommentViewSet

router = DefaultRouter()
router.register(r"posts", PostViewSet, basename="post")
router.register(r"comments", CommentViewSet, basename="comment")


urlpatterns = router.urls