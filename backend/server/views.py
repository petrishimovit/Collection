from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.viewsets import ViewSet


class PingViewSet(ViewSet):
    """
    Helpful class for internal health checks
    for when your server deploys. Typical of AWS
    applications behind ALB which does default 30
    second ping/health checks.
    """

    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        return Response(data={"status": "ok"}, status=HTTP_200_OK)
