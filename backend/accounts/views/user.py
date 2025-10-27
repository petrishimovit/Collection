from rest_framework import viewsets, permissions, decorators, response, status
from django.db.models import Prefetch
from accounts.models import User
from accounts.serializers.user import UserListSerializer, UserDetailSerializer
from accounts.serializers.profile import ProfileWriteSerializer


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /users/           -> list (public)
    /users/{id}/      -> retrieve (public)
    /users/{id}/follow (POST/DELETE) -> follow/unfollow (auth)
    /users/me (GET/PATCH) -> current user (auth), PATCH updates profile via ProfileWriteSerializer
    """
    queryset = User.objects.select_related("profile").prefetch_related(
        Prefetch("followers"), Prefetch("following")
    )
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        return UserDetailSerializer if self.action == "retrieve" else UserListSerializer

    @decorators.action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="follow",
    )
    def follow(self, request, pk=None):
        target = self.get_object()
        if target.id == request.user.id:
            return response.Response({"detail": "Cannot follow yourself."}, status=400)

        if request.method == "POST":
            created = request.user.follow(target)
            return response.Response(
                {"status": "followed" if created else "already_following"},
                status=status.HTTP_200_OK,
            )
        # DELETE
        deleted = request.user.unfollow(target)
        return response.Response(
            {"status": "unfollowed" if deleted else "not_following"},
            status=status.HTTP_200_OK,
        )

    @decorators.action(
        detail=False,
        methods=["get", "patch"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="me",
    )
    def me(self, request):
        if request.method == "GET":
            ser = UserDetailSerializer(request.user, context={"request": request})
            return response.Response(ser.data)

   
        profile_data = request.data.get("profile", {})
        if not isinstance(profile_data, dict):
            return response.Response(
                {"detail": "Provide data under 'profile' object."}, status=400
            )
        ser = ProfileWriteSerializer(
            request.user.profile, data=profile_data, partial=True, context={"request": request}
        )
        ser.is_valid(raise_exception=True)
        ser.save()
        # return fresh full detail
        out = UserDetailSerializer(request.user, context={"request": request})
        return response.Response(out.data, status=status.HTTP_200_OK)
