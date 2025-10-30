from __future__ import annotations
from pathlib import Path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .serializers import GameItemSerializer
from .services.search import GameSearchService

class GameSearchView(APIView):
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
            return Response({"detail": "Please provide query parameter ?q="}, status=status.HTTP_400_BAD_REQUEST)

        data = self.service.search_by_name(
            q=q,
            platform=platform,
            limit=1 if single else limit,
            offset=0 if single else offset,
            autoload_dir=self.DB_PATH,
        )

        items = data["items"]
        if single:
            return Response(items[0] if items else {}, status=status.HTTP_200_OK)
        return Response(items, status=status.HTTP_200_OK)
