from typing import Any, Dict
from django.http import Http404
from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions, decorators, response, status
from rest_framework.request import Request
from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiResponse, OpenApiExample, OpenApiParameter
)

from apps.accounts.schemas import FollowActionOut, ProfileOut, ProfileUpdateIn
from apps.accounts.pagination import DefaultPagination
from apps.accounts.permissions import IsSelfOrStaff
from apps.accounts.selectors.user import user_list_qs, following_qs, followers_qs
from apps.accounts.serializers.user import (
    UserListSerializer, UserDetailSerializer, MeMinimalSerializer,
)
from apps.accounts.serializers.profile import ProfileBaseSerializer, ProfileWriteSerializer
from apps.accounts.services.user import UserService

User = get_user_model()


@extend_schema_view(
    list=extend_schema(
        tags=["Users"],
        summary="List users",
        description="Retrieve a paginated list of active users with minimal profile info.",
        responses=UserListSerializer,
    ),
    retrieve=extend_schema(
        tags=["Users"],
        summary="Get user",
        description="Retrieve detailed information about a specific user (excluding email).",
        responses=UserDetailSerializer,
        parameters=[OpenApiParameter(name="id", location=OpenApiParameter.PATH, required=True)],
    ),
)
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """Users ViewSet Followers Logic Include"""
    permission_classes = [permissions.AllowAny]
    pagination_class = DefaultPagination

    def get_queryset(self):
        """Return queryset of active users."""
        return user_list_qs()

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        return UserDetailSerializer if self.action == "retrieve" else UserListSerializer

    def get_object(self):
        """Retrieve a user instance, ensuring it is active."""
        obj = super().get_object()
        if not obj.is_active:
            raise Http404
        return obj

    @extend_schema(
        tags=["Users"],
        summary="Follow or unfollow user",
        description="Toggle the follow status for the target user. Returns the action result.",
        examples=[
            OpenApiExample("Followed", value={"status": "followed"}),
            OpenApiExample("Unfollowed", value={"status": "unfollowed"}),
        ],
    )
    @decorators.action(
        detail=True,
        methods=["post"],
        url_path="follow",
        permission_classes=[permissions.IsAuthenticated],
    )
    def follow(self, request: Request, pk: str | None = None):
        """Toggle following another user."""
        target = self.get_object()
        try:
            res = UserService.toggle_follow(actor=request.user, target=target)
        except ValueError as e:
            if str(e) == "cannot_follow_self":
                return response.Response({"detail": "Cannot follow yourself."}, status=400)
            return response.Response({"detail": "Bad request."}, status=400)
        return response.Response({"status": res.status}, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Users"],
        summary="Get or update user profile",
        description=(
            "GET: Retrieve user's display name and basic profile info.\n"
            "PATCH/PUT: Update user's display name and profile fields."
        ),
        request=ProfileUpdateIn,
    )
    @decorators.action(
        detail=True,
        methods=["get", "patch", "put"],
        url_path="profile",
        permission_classes=[permissions.AllowAny],
    )
    def profile(self, request: Request, pk: str | None = None):
        """Get or update a user's profile."""
        user = self.get_object()

        if request.method == "GET":
            payload = {
                "display_name": user.display_name,
                "profile": ProfileBaseSerializer(user.profile, context={"request": request}).data,
            }
            return response.Response(payload, status=status.HTTP_200_OK)

        self.check_object_permissions(request, user)

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
        """Apply `IsSelfOrStaff` permission for profile update actions."""
        if self.action == "profile" and getattr(self.request, "method", "") in ("PATCH", "PUT"):
            return [IsSelfOrStaff()]
        return super().get_permissions()

    @extend_schema(
        tags=["Users"],
        summary="List user's following",
        description="Retrieve paginated list of users the given user follows.",
        responses=UserListSerializer,
        parameters=[OpenApiParameter(name="id", location=OpenApiParameter.PATH, required=True)]
    )
    @decorators.action(detail=True, methods=["get"], url_path="following", permission_classes=[permissions.AllowAny])
    def following(self, request: Request, pk: str | None = None):
        """Return list of users this user follows."""
        user = self.get_object()
        page = self.paginate_queryset(following_qs(user))
        ser = UserListSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(ser.data)

    @extend_schema(
        tags=["Users"],
        summary="Authenticated user info / Deactivate self",
        description="GET: Return minimal info about current user.\nDELETE: Deactivate current account.",
        responses={200: MeMinimalSerializer, 204: OpenApiResponse(description="Deactivated")},
    )
    @decorators.action(detail=False, methods=["get", "delete"], url_path="me", permission_classes=[permissions.IsAuthenticated])
    def me(self, request: Request):
        """Return current user's info or deactivate their account."""
        if request.method == "DELETE":
            UserService.deactivate_self(user=request.user)
            return response.Response({"status": "deactivated"}, status=status.HTTP_204_NO_CONTENT)
        ser = MeMinimalSerializer(request.user, context={"request": request})
        return response.Response(ser.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Users"],
        summary="My following list",
        description="Retrieve paginated list of users the authenticated user follows.",
        responses=UserListSerializer,
    )
    @decorators.action(detail=False, methods=["get"], url_path="me/following", permission_classes=[permissions.IsAuthenticated])
    def my_following(self, request: Request):
        """Return list of users the current user follows."""
        page = self.paginate_queryset(following_qs(request.user))
        ser = UserListSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(ser.data)

    @extend_schema(
        tags=["Users"],
        summary="User followers",
        description="Retrieve paginated list of users who follow the given user.",
        responses=UserListSerializer,
        parameters=[OpenApiParameter(name="id", location=OpenApiParameter.PATH, required=True)],
    )
    @decorators.action(detail=True, methods=["get"], url_path="followers", permission_classes=[permissions.AllowAny])
    def followers(self, request: Request, pk: str | None = None):
        """Return list of users following this user."""
        user = self.get_object()
        page = self.paginate_queryset(followers_qs(user))
        ser = UserListSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(ser.data)

    @extend_schema(
        tags=["Users"],
        summary="My followers list",
        description="Retrieve paginated list of users who follow the authenticated user.",
        responses=UserListSerializer,
    )
    @decorators.action(detail=False, methods=["get"], url_path="me/followers", permission_classes=[permissions.IsAuthenticated])
    def my_followers(self, request: Request):
        """Return list of users who follow the current user."""
        page = self.paginate_queryset(followers_qs(request.user))
        ser = UserListSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(ser.data)
