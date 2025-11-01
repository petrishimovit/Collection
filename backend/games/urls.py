from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import GameSearchView, PricechartingSearchView, PricechartingItemView , PriceChartingConnectViewSet


router = DefaultRouter()
router.register(r"integrations/pricecharting", PriceChartingConnectViewSet, basename="pricecharting-connect")

urlpatterns = [
    path("search/", GameSearchView.as_view(), name="games-search"),
    path("integrations/pricecharting/search/", PricechartingSearchView.as_view()),
    path("integrations/pricecharting/item/", PricechartingItemView.as_view()),
    path("", include(router.urls)),
]
