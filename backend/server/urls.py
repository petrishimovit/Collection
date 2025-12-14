from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import PingViewSet

router = SimpleRouter()
router.register(r"health", PingViewSet, basename="health")

urlpatterns = [
    path("", include(router.urls)),
]
