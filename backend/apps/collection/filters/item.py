from django_filters import rest_framework as filters

from apps.collection.models import Item


class ItemFilter(filters.FilterSet):
    """
    filters for Item list/search endpoint.
    """

    for_sale = filters.BooleanFilter(field_name="for_sale")

    class Meta:
        model = Item
        fields = (
            "for_sale",
            
        )
