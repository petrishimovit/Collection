from django.urls import path
from .views import GameSearchView,PricechartingSearchView, PricechartingItemView

urlpatterns = [
    path("search/", GameSearchView.as_view(), name="games-search"),
    path("integrations/pricecharting/search/", PricechartingSearchView.as_view()),
    path("integrations/pricecharting/item/", PricechartingItemView.as_view()),
]
