from django.urls import path, include
from rest_framework.routers import DefaultRouter
from posts.views.post import PostViewSet

router = DefaultRouter()
router.register(r"posts", PostViewSet, basename="post")

urlpatterns = router.urls