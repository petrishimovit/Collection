from __future__ import annotations

from pathlib import Path

from rest_framework import views, response, permissions, status, serializers
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .serializers import GameItemSerializer
from .services.search import GameSearchService
from .integrations.pricecharting import PricechartingClient, Region


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


class SearchQuerySerializer(serializers.Serializer):
    q = serializers.CharField(max_length=200)
    region = serializers.ChoiceField(
        choices=["all", "japan", "ntsc", "pal"],
        required=False,
        default="all",
    )
    limit = serializers.IntegerField(required=False, min_value=1, max_value=50, default=10)


class ItemQuerySerializer(serializers.Serializer):
    url = serializers.URLField(required=False)
    slug = serializers.CharField(required=False)

    def validate(self, data):
        if not data.get("url") and not data.get("slug"):
            raise serializers.ValidationError("Provide `url` or `slug`.")
        return data


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
        region: Region = params.validated_data["region"]
        limit = params.validated_data["limit"]
        items = PricechartingClient.search(q=q, region=region, limit=limit)
        return response.Response([i.__dict__ for i in items])


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
        token = params.validated_data.get("url") or params.validated_data.get("slug")
        data = PricechartingClient.item_details(token)
        return response.Response(data)
