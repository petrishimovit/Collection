from __future__ import annotations

from pathlib import Path

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions, response, status, views

from apps.games.serializers import GameItemSerializer
from apps.games.services.search import GameSearchService


class GameSearchView(views.APIView):
    """
    Search endpoint for local GamesDB (static JSON database).
    """

    permission_classes = [permissions.AllowAny]
    DB_PATH = Path(__file__).resolve().parent.parent / "gamesdb"
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
        """
        perform substring search over local games registry.
        """
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
