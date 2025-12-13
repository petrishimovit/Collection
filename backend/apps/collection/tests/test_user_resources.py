from datetime import datetime, timedelta

import pytest
from django.utils import timezone

from apps.accounts.models import Follow, User
from apps.collection.models import Collection, Item

pytestmark = pytest.mark.django_db


def create_user(email: str, name: str) -> User:
    return User.objects.create_user(
        email=email,
        password="stringst",
        display_name=name,
    )


def create_collection(owner: User, name: str, privacy: str) -> Collection:
    return Collection.objects.create(
        owner=owner,
        name=name,
        privacy=privacy,
    )


def create_item(
    collection: Collection,
    name: str,
    item_privacy: str,
    for_sale: bool = False,
) -> Item:
    return Item.objects.create(
        collection=collection,
        name=name,
        privacy=item_privacy,
        for_sale=for_sale,
    )


def test_user_collections_list_respects_privacy_for_anonymous(api_client):
    # Arrange
    owner = create_user("owner@example.com", "owner")

    col_public = create_collection(owner, "Public", Collection.PRIVACY_PUBLIC)
    col_follow = create_collection(owner, "Following", Collection.PRIVACY_FOLLOWING)
    col_private = create_collection(owner, "Private", Collection.PRIVACY_PRIVATE)

    url = f"/users/{str(owner.id)}/collections/"

    # Act
    res = api_client.get(url)

    # Assert
    assert res.status_code == 200
    names = {c["name"] for c in res.data["results"]}
    assert col_public.name in names
    assert col_follow.name not in names
    assert col_private.name not in names


def test_user_collections_list_owner_sees_all(api_client):
    # Arrange
    owner = create_user("owner2@example.com", "owner2")

    col_public = create_collection(owner, "Public2", Collection.PRIVACY_PUBLIC)
    col_follow = create_collection(owner, "Following2", Collection.PRIVACY_FOLLOWING)
    col_private = create_collection(owner, "Private2", Collection.PRIVACY_PRIVATE)

    api_client.force_authenticate(owner)
    url = f"/users/{str(owner.id)}/collections/"

    # Act
    res = api_client.get(url)

    # Assert
    assert res.status_code == 200
    names = {c["name"] for c in res.data["results"]}
    assert col_public.name in names
    assert col_follow.name in names
    assert col_private.name in names


def test_user_collections_list_following_only_visible_when_owner_follows_viewer(api_client):
    # Arrange
    owner = create_user("owner3@example.com", "owner3")
    viewer = create_user("viewer3@example.com", "viewer3")

    col_public = create_collection(owner, "Pub3", Collection.PRIVACY_PUBLIC)
    col_follow = create_collection(owner, "Follow3", Collection.PRIVACY_FOLLOWING)

    # owner -> viewer (owner__following_relations__following=viewer)
    Follow.objects.create(follower=owner, following=viewer)

    api_client.force_authenticate(viewer)
    url = f"/users/{str(owner.id)}/collections/"

    # Act
    res = api_client.get(url)

    # Assert
    assert res.status_code == 200
    names = {c["name"] for c in res.data["results"]}
    assert col_public.name in names
    assert col_follow.name in names


def test_user_items_list_respects_privacy_for_anonymous(api_client):
    # Arrange
    owner = create_user("owner4@example.com", "owner4")

    col_public = create_collection(owner, "Pub4", Collection.PRIVACY_PUBLIC)
    col_follow = create_collection(owner, "Follow4", Collection.PRIVACY_FOLLOWING)
    col_private = create_collection(owner, "Priv4", Collection.PRIVACY_PRIVATE)

    i_pub_pub = create_item(col_public, "pub_pub", Item.PRIVACY_PUBLIC)
    i_pub_follow = create_item(col_public, "pub_follow", Item.PRIVACY_FOLLOWING)
    i_pub_priv = create_item(col_public, "pub_priv", Item.PRIVACY_PRIVATE)

    i_follow_pub = create_item(col_follow, "follow_pub", Item.PRIVACY_PUBLIC)
    i_follow_follow = create_item(col_follow, "follow_follow", Item.PRIVACY_FOLLOWING)

    i_priv_pub = create_item(col_private, "priv_pub", Item.PRIVACY_PUBLIC)

    url = f"/users/{str(owner.id)}/items/"

    # Act
    res = api_client.get(url)

    # Assert
    assert res.status_code == 200
    names = {i["name"] for i in res.data["results"]}

    assert i_pub_pub.name in names

    assert i_pub_follow.name not in names
    assert i_pub_priv.name not in names
    assert i_follow_pub.name not in names
    assert i_follow_follow.name not in names
    assert i_priv_pub.name not in names


def test_user_items_list_owner_sees_all(api_client):
    # Arrange
    owner = create_user("owner5@example.com", "owner5")

    col_public = create_collection(owner, "Pub5", Collection.PRIVACY_PUBLIC)
    col_follow = create_collection(owner, "Follow5", Collection.PRIVACY_FOLLOWING)
    col_private = create_collection(owner, "Priv5", Collection.PRIVACY_PRIVATE)

    i1 = create_item(col_public, "i1", Item.PRIVACY_PUBLIC)
    i2 = create_item(col_follow, "i2", Item.PRIVACY_FOLLOWING)
    i3 = create_item(col_private, "i3", Item.PRIVACY_PRIVATE)

    api_client.force_authenticate(owner)
    url = f"/users/{str(owner.id)}/items/"

    # Act
    res = api_client.get(url)

    # Assert
    assert res.status_code == 200
    names = {i["name"] for i in res.data["results"]}
    assert i1.name in names
    assert i2.name in names
    assert i3.name in names


def test_user_items_list_for_sale_filter(api_client):
    # Arrange
    owner = create_user("owner6@example.com", "owner6")
    col_public = create_collection(owner, "Pub6", Collection.PRIVACY_PUBLIC)

    i_sale = create_item(col_public, "sale", Item.PRIVACY_PUBLIC, for_sale=True)
    i_not_sale = create_item(col_public, "nosale", Item.PRIVACY_PUBLIC, for_sale=False)

    api_client.force_authenticate(owner)
    base_url = f"/users/{str(owner.id)}/items/"

    # Act
    res_true = api_client.get(f"{base_url}?for_sale=true")
    res_false = api_client.get(f"{base_url}?for_sale=false")

    # Assert
    assert res_true.status_code == 200
    names_true = {i["name"] for i in res_true.data["results"]}
    assert i_sale.name in names_true
    assert i_not_sale.name not in names_true

    assert res_false.status_code == 200
    names_false = {i["name"] for i in res_false.data["results"]}
    assert i_sale.name not in names_false
    assert i_not_sale.name in names_false


def test_user_heatmap_returns_data_for_owner_collections_and_items(api_client):
    # Arrange
    owner = create_user("owner7@example.com", "owner7")
    viewer = create_user("viewer7@example.com", "viewer7")

    col = create_collection(owner, "Pub7", Collection.PRIVACY_PUBLIC)
    item = create_item(col, "it7", Item.PRIVACY_PUBLIC)

    # Зафиксируем дату, чтобы предсказуемо проверить
    target_day = timezone.now().date() - timedelta(days=1)
    target_dt = datetime.combine(target_day, datetime.min.time()).replace(tzinfo=timezone.utc)

    Collection.objects.filter(pk=col.pk).update(
        created_at=target_dt,
        updated_at=target_dt,
    )
    Item.objects.filter(pk=item.pk).update(
        created_at=target_dt,
        updated_at=target_dt,
    )

    api_client.force_authenticate(viewer)
    url = f"/users/{str(owner.id)}/heatmap/"

    # Act
    res = api_client.get(url)

    # Assert
    assert res.status_code == 200
    assert isinstance(res.data, list)
    dates = {row["date"] for row in res.data}
    assert str(target_day) in dates or target_day in dates
