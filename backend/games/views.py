from __future__ import annotations

from pathlib import Path

from rest_framework import views, response, permissions, status, serializers , viewsets ,decorators

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.db.models import Count


from collection.models import Item
from .models import PriceChartingConnect

from .serializers import GameItemSerializer , SearchQuerySerializer , ItemQuerySerializer , PriceChartingConnectSerializer , UnbindSerializer , BindSerializer
from .services.search import GameSearchService
from .services.pricecharting import PricechartingService 


class GameSearchView(views.APIView):
    permission_classes = [permissions.AllowAny]
    DB_PATH = Path(__file__).resolve().parent / "gamesdb"
    service = GameSearchService()

    @extend_schema(
        summary="Game search",
        parameters=[
            OpenApiParameter("q", OpenApiTypes.STR, OpenApiParameter.QUERY, required=True),
            OpenApiParameter("platform", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("single", OpenApiTypes.BOOL, OpenApiParameter.QUERY),
            OpenApiParameter("limit", OpenApiTypes.INT, OpenApiParameter.QUERY),
            OpenApiParameter("offset", OpenApiTypes.INT, OpenApiParameter.QUERY),
        ],
        responses={200: GameItemSerializer(many=True)},
    )
    def get(self, request):
        q = request.query_params.get("q", "")
        platform = request.query_params.get("platform")
        single = str(request.query_params.get("single", "")).lower() in ("1", "true", "yes")

        try:
            limit = max(1, min(int(request.query_params.get("limit") or 50), 50))
        except ValueError:
            limit = 50
        try:
            offset = max(0, int(request.query_params.get("offset") or 0))
        except ValueError:
            offset = 0

        if not q.strip():
            return response.Response(
                {"detail": "Please provide query parameter ?q="},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = self.service.search_by_name(
            q=q,
            platform=platform,
            limit=1 if single else limit,
            offset=0 if single else offset,
            autoload_dir=self.DB_PATH,
        )

        items = data["items"]
        if single:
            return response.Response(items[0] if items else {}, status=status.HTTP_200_OK)
        return response.Response(items, status=status.HTTP_200_OK)




@extend_schema(
    summary="Search PriceCharting",
    parameters=[
        OpenApiParameter("q", str, OpenApiParameter.QUERY, required=True),
        OpenApiParameter("region", str, OpenApiParameter.QUERY, description="all | japan | ntsc | pal"),
        OpenApiParameter("limit", int, OpenApiParameter.QUERY, description="1..50"),
    ],
    tags=["PriceCharting"],
)
class PricechartingSearchView(views.APIView):
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
    GET /games/integrations/pricecharting/ -> get all integrations
    GET /games/integrations/pricecharting/{id}/ -> get by id
    POST /integrations/pricecharting/bind/   -> {item_id, url} (auth required)
    POST /integrations/pricecharting/unbind/ -> {item_id}     (auth required)
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = PriceChartingConnectSerializer
    queryset = PricechartingService.public_qs()  #

    @decorators.action(
        methods=["post"], detail=False, url_path="bind",
        permission_classes=[permissions.IsAuthenticated],
        serializer_class=BindSerializer,
    )
    def bind(self, request):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        obj = ser.save()  
        obj = (
            PriceChartingConnect.objects
            .filter(id=obj.id)
            .annotate(items_count=Count("items"))
            .first()
        )
        data = PriceChartingConnectSerializer(obj, context=self.get_serializer_context()).data
        return response.Response(data, status=status.HTTP_200_OK)

    @decorators.action(
        methods=["post"], detail=False, url_path="unbind",
        permission_classes=[permissions.IsAuthenticated],
        serializer_class=UnbindSerializer,
    )
    def unbind(self, request):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return response.Response({"status": "ok"}, status=status.HTTP_200_OK)