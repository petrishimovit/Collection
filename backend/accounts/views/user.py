from typing import Any, Dict

from django.http import Http404
from django.contrib.auth import get_user_model

from rest_framework import viewsets, permissions, decorators, response, status , mixins
from rest_framework.request import Request

from accounts.pagination import DefaultPagination
from accounts.permissions import IsSelfOrStaff
from accounts.selectors.user import user_list_qs, following_qs
from accounts.serializers.user import (
    UserListSerializer,
    UserDetailSerializer,
    MeMinimalSerializer,
)
from accounts.serializers.profile import (
    ProfileBaseSerializer,
    ProfileWriteSerializer,
)
from accounts.services.user import UserService


User = get_user_model()


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Users API (only active users are visible):

    - GET    /users/                    -> list (mini profile)
    - GET    /users/{id}/               -> detail (no email)
    - POST   /users/{id}/follow/        -> toggle follow/unfollow
    - GET    /users/{id}/profile/       -> {"display_name", "profile": mini}
    - PATCH  /users/{id}/profile/       -> update own display_name + profile
    - PUT    /users/{id}/profile/       -> replace own display_name + profile
    - GET    /users/{id}/following/     -> list following (only active), paginated
    - GET    /users/me/                 -> minimal self info (id, display_name, mini)
    - GET    /users/me/following/       -> my following (only active), paginated
    - DELETE /users/me/                 -> soft-delete self (is_active=False)
    """

    permission_classes = [permissions.AllowAny]
    pagination_class = DefaultPagination

    def get_queryset(self):
        return user_list_qs()  # only active users

    def get_serializer_class(self):
        return UserDetailSerializer if self.action == "retrieve" else UserListSerializer

    def get_object(self):
        obj = super().get_object()
        if not obj.is_active:
            raise Http404
        return obj

    @decorators.action(
        detail=True,
        methods=["post"],
        url_path="follow",
        permission_classes=[permissions.IsAuthenticated],
    )
    def follow(self, request: Request, pk: str | None = None):
        target = self.get_object()
        try:
            res = UserService.toggle_follow(actor=request.user, target=target)
        except ValueError as e:
            if str(e) == "cannot_follow_self":
                return response.Response({"detail": "Cannot follow yourself."}, status=400)
            return response.Response({"detail": "Bad request."}, status=400)
        return response.Response({"status": res.status}, status=status.HTTP_200_OK)

    @decorators.action(
        detail=True,
        methods=["get", "patch", "put"],
        url_path="profile",
        permission_classes=[permissions.AllowAny],
    )
    def profile(self, request: Request, pk: str | None = None):
        user = self.get_object()

        if request.method == "GET":
            payload = {
                "display_name": user.display_name,
                "profile": ProfileBaseSerializer(user.profile, context={"request": request}).data,
            }
            return response.Response(payload, status=status.HTTP_200_OK)

        self.check_object_permissions(request, user)  # IsSelfOrStaff via get_permissions()

        raw: Dict[str, Any] = request.data if isinstance(request.data, dict) else {}
        display_name = raw.get("display_name", None)
        profile_data = raw.get("profile", {})

        write_ser = ProfileWriteSerializer(
            user.profile,
            data=profile_data,
            partial=(request.method == "PATCH"),
            context={"request": request},
        )
        write_ser.is_valid(raise_exception=True)

        UserService.update_display_and_profile(
            user=user,
            display_name=display_name,
            profile_data=write_ser.validated_data,
        )
        write_ser.save()

        out = {
            "display_name": user.display_name,
            "profile": ProfileBaseSerializer(user.profile, context={"request": request}).data,
        }
        return response.Response(out, status=status.HTTP_200_OK)

    def get_permissions(self):
        if self.action == "profile" and getattr(self.request, "method", "") in ("PATCH", "PUT"):
            return [IsSelfOrStaff()]
        return super().get_permissions()

    @decorators.action(
        detail=True,
        methods=["get"],
        url_path="following",
        permission_classes=[permissions.AllowAny],
    )
    def following(self, request: Request, pk: str | None = None):
        user = self.get_object()
        page = self.paginate_queryset(following_qs(user))
        ser = UserListSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(ser.data)

    @decorators.action(
        detail=False,
        methods=["get", "delete"],
        url_path="me",
        permission_classes=[permissions.IsAuthenticated],
    )
    def me(self, request: Request):
        if request.method == "DELETE":
            UserService.deactivate_self(user=request.user)
            return response.Response({"status": "deactivated"}, status=status.HTTP_204_NO_CONTENT)

        ser = MeMinimalSerializer(request.user, context={"request": request})
        return response.Response(ser.data, status=status.HTTP_200_OK)

    @decorators.action(
        detail=False,
        methods=["get"],
        url_path="me/following",
        permission_classes=[permissions.IsAuthenticated],
    )
    def my_following(self, request: Request):
        page = self.paginate_queryset(following_qs(request.user))
        ser = UserListSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(ser.data)


