from typing import Optional

from django.contrib.auth import get_user_model
from django.db.models import (
    Q,
    Count,
    QuerySet,
    Sum,
    DecimalField,
    Value,
)
from django.db.models.functions import Coalesce

from apps.collection.models import Collection

User = get_user_model()


def _base_collection_qs() -> QuerySet[Collection]:
    """
    Base queryset for collections with annotations:
      - items_count
      - total_current_value
      - total_purchase_price
    """
    return (
        Collection.objects
        .select_related("owner")
        .annotate(
            items_count=Count("items"),
            total_current_value=Coalesce(
                Sum("items__current_value"),
                Value(0),
                output_field=DecimalField(max_digits=15, decimal_places=2),
            ),
            total_purchase_price=Coalesce(
                Sum("items__purchase_price"),
                Value(0),
                output_field=DecimalField(max_digits=15, decimal_places=2),
            ),
        )
    )


def get_public_collections() -> QuerySet[Collection]:
    """
    Public collections visible to any user.
    """
    return _base_collection_qs().filter(
        privacy=Collection.PRIVACY_PUBLIC,
    )


def get_collections_for_user(user: Optional[User]) -> QuerySet[Collection]:
    """
    Collections visible to the given user.

    Anonymous:
        - only public collections

    Authenticated:
        - own collections (any privacy)
        - public collections of others
        - following_only collections of owners who follow the user:
              Follow(follower=owner, following=user)
    """
    qs = _base_collection_qs()

    if not user or not user.is_authenticated:
        return qs.filter(privacy=Collection.PRIVACY_PUBLIC)

    own = Q(owner=user)

    public = Q(privacy=Collection.PRIVACY_PUBLIC)

    following_only = Q(
        privacy=Collection.PRIVACY_FOLLOWING,
        owner__following_relations__following=user,
    )

    return qs.filter(own | public | following_only).distinct()


def get_user_collections(user: User) -> QuerySet[Collection]:
    """
    All collections owned by the user (no privacy restriction).
    """
    return _base_collection_qs().filter(owner=user)


def get_collection_for_user(
    user: Optional[User],
    collection_id: int,
) -> Optional[Collection]:
    """
    Single collection visible to the user.
    """
    qs = get_collections_for_user(user)
    try:
        return qs.get(id=collection_id)
    except Collection.DoesNotExist:
        return None


def get_feed_collections_for_user(user: User) -> QuerySet[Collection]:
    """
    Collections for the user's feed.

    Rules:
        - only collections of users current user follows:
              Follow(follower=user, following=owner)
        - include PUBLIC collections
        - include FOLLOWING_ONLY collections only if follow is mutual:
              user follows owner AND owner follows user
    """
    if not user.is_authenticated:
        return _base_collection_qs().none()

    qs = _base_collection_qs()

    follows_owner = Q(owner__follower_relations__follower=user)

    owner_follows_user = Q(owner__following_relations__following=user)

    public = Q(privacy=Collection.PRIVACY_PUBLIC)

    following_only = Q(privacy=Collection.PRIVACY_FOLLOWING) & owner_follows_user

    return qs.filter(follows_owner & (public | following_only)).distinct()


def get_collections_for_user_profile(
    viewer: Optional[User],
    owner_id: str,
) -> QuerySet[Collection]:
    """
    Collections owned by the given user and visible to the viewer.

    - viewer: user who is requesting the data (may be anonymous)
    - owner_id: target user ID whose collections we want to list

    Privacy rules are inherited from get_collections_for_user(viewer).
    """
    visible_qs = get_collections_for_user(viewer)
    return visible_qs.filter(owner_id=owner_id)
