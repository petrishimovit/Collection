from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.games.views.games import GameSearchView
from apps.games.views.pricecharting import (
    PriceChartingConnectViewSet,
    PricechartingItemView,
    PricechartingSearchView,
)

router = DefaultRouter()
router.register(
    r"integrations/pricecharting",
    PriceChartingConnectViewSet,
    basename="pricecharting-connect",
)

urlpatterns = [
    path("search/", GameSearchView.as_view(), name="games-search"),
    path(
        "integrations/pricecharting/search/",
        PricechartingSearchView.as_view(),
        name="pricecharting-search",
    ),
    path(
        "integrations/pricecharting/item/",
        PricechartingItemView.as_view(),
        name="pricecharting-item",
    ),
    path("", include(router.urls)),
]
