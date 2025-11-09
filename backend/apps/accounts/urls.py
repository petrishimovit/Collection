from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter

from apps.accounts.views.auth import RegisterView 
from apps.accounts.views.user import UserViewSet


app_name = "accounts"

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")


urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token-obtain"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    

  
    path("", include(router.urls)),
]
