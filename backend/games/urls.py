from django.urls import path
from .views import GameSearchView

urlpatterns = [
    path("search/", GameSearchView.as_view(), name="games-search"),
]
