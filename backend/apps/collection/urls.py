from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.collection.views.collection import CollectionViewSet
from apps.collection.views.item import ItemViewSet
from apps.collection.views.user_resources import (
    UserCollectionsListView,
    UserHeatmapView,
    UserItemsListView,
)
from apps.collection.views.wishlist import (
    MyWishListCreateView,
    UserWishListListView,
    WishListDestroyView,
)

router = DefaultRouter()
router.register(r"collections", CollectionViewSet, basename="Collection")
router.register(r"items", ItemViewSet, basename="Item")


urlpatterns = router.urls + [
    path(
        "users/<uuid:user_id>/wishlist/",
        UserWishListListView.as_view(),
    ),
    path(
        "users/me/wishlist/",
        MyWishListCreateView.as_view(),
    ),
    path(
        "users/wishlist/<uuid:pk>/",
        WishListDestroyView.as_view(),
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
