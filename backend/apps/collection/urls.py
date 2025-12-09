from rest_framework.routers import DefaultRouter
from django.urls import path
from apps.collection.views.collection import CollectionViewSet
from apps.collection.views.item import ItemViewSet
from apps.collection.views.favorite import (
    UserFavoritesListView,
    MyFavoritesCreateView,
    FavoriteDestroyView,
)
from apps.collection.views.user_resources import UserCollectionsListView , UserItemsListView , UserHeatmapView


router = DefaultRouter()
router.register(r"collections", CollectionViewSet, basename="Collection")
router.register(r"items", ItemViewSet, basename="Item")



urlpatterns = router.urls + [
    path(
        "users/<uuid:user_id>/favorites/",
        UserFavoritesListView.as_view()
    ),
    path(
        "users/me/favorites/",
        MyFavoritesCreateView.as_view(),
    ),
    path(
        "users/<uuid:user_id>/collections/",
        UserCollectionsListView.as_view(),
    ),
    path(
        "users/<uuid:user_id>/items/",
        UserItemsListView.as_view(),
    ),
    path(
        "users/<uuid:user_id>/heatmap/",
        UserHeatmapView.as_view(),
    ),
]


