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
    tags=["Games"],
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
)
class PricechartingSearchView(views.APIView):
    """
    proxy endpoint to search games on pricecharting.com
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        params = SearchQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)

        items = PricechartingService.search_items(**params.validated_data)
        return response.Response(items)


@extend_schema(
    summary="Get PriceCharting item details",
    tags=["Games"],
    parameters=[
        OpenApiParameter("url", str, OpenApiParameter.QUERY),
        OpenApiParameter("slug", str, OpenApiParameter.QUERY),
    ],
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


@extend_schema(tags=["Games"])
class PriceChartingConnectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    read-only viewSet for pricechartingconnect objects.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = PriceChartingConnectSerializer
    queryset = PricechartingService.public_qs()

    @extend_schema(summary="List PriceCharting connects")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Retrieve PriceCharting connect")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @decorators.action(
        methods=["post"],
        detail=False,
        url_path="bind",
        permission_classes=[permissions.IsAuthenticated],
        serializer_class=BindSerializer,
    )
    @extend_schema(
        summary="Bind a collection item to PriceCharting by URL",
        tags=["Games"],
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
    @extend_schema(
        summary="Unbind a collection item from PriceCharting",
        tags=["Games"],
    )
    def unbind(self, request):
        """
        unbind a collection item from pricecharting
        """
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return response.Response({"status": "ok"}, status=status.HTTP_200_OK)
