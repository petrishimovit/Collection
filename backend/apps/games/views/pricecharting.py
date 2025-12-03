from __future__ import annotations

from django.db.models import Count
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import decorators, permissions, response, status, views, viewsets

from apps.games.models import PriceChartingConnect
from apps.games.serializers import (
    BindSerializer,
    ItemQuerySerializer,
    PriceChartingConnectSerializer,
    SearchQuerySerializer,
    UnbindSerializer,
)
from apps.games.services.pricecharting import PricechartingService


@extend_schema(
    summary="Search PriceCharting",
    parameters=[
        OpenApiParameter("q", str, OpenApiParameter.QUERY, required=True),
        OpenApiParameter(
            "region",
            str,
            OpenApiParameter.QUERY,
            description="Region filter: all | japan | ntsc | pal",
        ),
        OpenApiParameter(
            "limit",
            int,
            OpenApiParameter.QUERY,
            description="Number of results to return (1..50)",
        ),
    ],
    tags=["PriceCharting"],
)
class PricechartingSearchView(views.APIView):
    """
    proxy endpoint to search games on pricecharting.com
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        params = SearchQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)

        q = params.validated_data["q"]
        region = params.validated_data["region"]
        limit = params.validated_data["limit"]

        items = PricechartingService.search_items(q=q, region=region, limit=limit)
        return response.Response(items)
    

@extend_schema(
    summary="Get PriceCharting item details",
    parameters=[
        OpenApiParameter("url", str, OpenApiParameter.QUERY),
        OpenApiParameter("slug", str, OpenApiParameter.QUERY),
    ],
    tags=["PriceCharting"],
)
class PricechartingItemView(views.APIView):
    """
    proxy endpoint to fetch details for a single pricecharting item.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        params = ItemQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)

        url = params.validated_data.get("url")
        slug = params.validated_data.get("slug")

        data = PricechartingService.get_item_details(url=url, slug=slug)
        return response.Response(data)


class PriceChartingConnectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    read-only viewSet for pricechartingconnect objects.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = PriceChartingConnectSerializer
    queryset = PricechartingService.public_qs()

    @decorators.action(
        methods=["post"],
        detail=False,
        url_path="bind",
        permission_classes=[permissions.IsAuthenticated],
        serializer_class=BindSerializer,
    )
    def bind(self, request):
        """
        bind a collection item to pricecharting by url
        """
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        obj = ser.save()

        obj = (
            PriceChartingConnect.objects.filter(id=obj.id)
            .annotate(items_count=Count("items"))
            .first()
        )
        data = PriceChartingConnectSerializer(
            obj,
            context=self.get_serializer_context(),
        ).data
        return response.Response(data, status=status.HTTP_200_OK)

    @decorators.action(
        methods=["post"],
        detail=False,
        url_path="unbind",
        permission_classes=[permissions.IsAuthenticated],
        serializer_class=UnbindSerializer,
    )
    def unbind(self, request):
        """
        unbind a collection item from pricecharting
        """
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return response.Response({"status": "ok"}, status=status.HTTP_200_OK)
