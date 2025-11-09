from django.urls import path, include
from . import views


from rest_framework import routers
router = routers.DefaultRouter()
router.register('ping', views.PingViewSet, basename="ping")

urlpatterns = [
    path('api/', include(router.urls))
]

"""
- For the first view, you send the refresh token to get a new access token.
- For the second view, you send the client credentials (username and password)
  to get BOTH a new access and refresh token.
"""
