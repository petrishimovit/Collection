from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter

from accounts.views.auth import RegisterView, MeView  
from accounts.views.user import UserViewSet
from accounts.views.profile import ProfileViewSet

app_name = "accounts"

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"profiles", ProfileViewSet, basename="profile")

urlpatterns = [
    # Auth endpoints
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token-obtain"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    # Current user endpoint
    path("me/", MeView.as_view(), name="me"),

    # Routers (users, profiles)
    path("", include(router.urls)),
]
