from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts.models import User
from apps.collection.models import Collection, Item, WishList

pytestmark = pytest.mark.django_db


def create_user(email: str, name: str = "user"):
    return User.objects.create_user(
        email=email,
        password="stringst",
        display_name=name,
    )


def create_collection(owner: User, name: str = "Test collection"):
    return Collection.objects.create(
        owner=owner,
        name=name,
    )


def create_item(collection: Collection, name: str = "Test item"):
    return Item.objects.create(
        collection=collection,
        name=name,
    )


def test_user_wishlist_list_returns_only_given_user(api_client):
    # Arrange
    user1 = create_user("user1@example.com", "user1")
    user2 = create_user("user2@example.com", "user2")

    col = create_collection(user1)
    item = create_item(col)

    fav1 = WishList.objects.create(
        user=user1,
        kind=WishList.Kind.ITEM,
        item=item,
        title="u1_fav",
    )
    WishList.objects.create(
        user=user2,
        kind=WishList.Kind.ITEM,
        item=item,
        title="u2_fav",
    )

    url = f"/users/{str(user1.id)}/wishlist/"

    # Act
    res = api_client.get(url)

    # Assert
    assert res.status_code == 200
    assert res.data["count"] == 1
    assert res.data["results"][0]["id"] == str(fav1.id)


def test_user_wishlist_list_supports_ordering(api_client):
    # Arrange
    user = create_user("u@example.com", "u")
    col = create_collection(user)
    item_a = create_item(col, "A")
    item_b = create_item(col, "B")

    fav_old = WishList.objects.create(
        user=user,
        kind=WishList.Kind.ITEM,
        item=item_a,
        title="old",
    )
    fav_new = WishList.objects.create(
        user=user,
        kind=WishList.Kind.ITEM,
        item=item_b,
        title="new",
    )

    WishList.objects.filter(pk=fav_old.pk).update(created_at=timezone.now() - timedelta(days=1))
    WishList.objects.filter(pk=fav_new.pk).update(created_at=timezone.now())

    url = f"/users/{str(user.id)}/wishlist/"

    # Act
    res_default = api_client.get(url)
    res_created = api_client.get(url, {"ordering": "created_at"})

    # Assert
    assert res_default.status_code == 200
    ids_default = [r["id"] for r in res_default.data["results"]]
    assert ids_default == [str(fav_new.id), str(fav_old.id)]

    # Assert
    assert res_created.status_code == 200
    ids_created = [r["id"] for r in res_created.data["results"]]
    assert ids_created == [str(fav_old.id), str(fav_new.id)]


def test_create_wishlist_item_returns_400_for_now(api_client):
    # Arrange
    user = create_user("user@example.com", "user")
    owner = create_user("owner@example.com", "owner")

    col = create_collection(owner)
    item = create_item(col, "Item A")

    api_client.force_authenticate(user)
    url = "/users/me/wishlist/"

    payload = {"kind": "item", "item_id": str(item.id)}

    # Act
    res = api_client.post(url, payload, format="json")

    # Assert
    assert res.status_code == 400


def test_create_wishlist_collection_returns_400_for_now(api_client):
    # Arrange
    user = create_user("user@example.com", "user")
    owner = create_user("owner@example.com", "owner")

    col = create_collection(owner, "Foreign collection")

    api_client.force_authenticate(user)
    url = "/users/me/wishlist/"

    payload = {"kind": "collection", "collection_id": str(col.id)}

    # Act
    res = api_client.post(url, payload, format="json")

    # Assert
    assert res.status_code == 400


def test_create_wishlist_custom_success(api_client):
    # Arrange
    user = create_user("user@example.com", "user")

    api_client.force_authenticate(user)
    url = "/users/me/wishlist/"

    payload = {
        "kind": "custom",
        "title": "Rare Cart",
        "external_url": "https://example.com/auction/123",
    }

    # Act
    res = api_client.post(url, payload, format="json")

    # Assert
    assert res.status_code == 201
    fav = WishList.objects.first()
    assert fav.user == user
    assert fav.kind == WishList.Kind.CUSTOM
    assert fav.title == "Rare Cart"
    assert fav.item is None
    assert fav.collection is None


def test_cannot_wishlist_own_item(api_client):
    # Arrange
    owner = create_user("owner@example.com", "owner")
    col = create_collection(owner)
    item = create_item(col)

    api_client.force_authenticate(owner)
    url = "/users/me/wishlist/"

    payload = {"kind": "item", "item_id": str(item.id)}

    # Act
    res = api_client.post(url, payload, format="json")

    # Assert
    assert res.status_code == 400
    assert WishList.objects.count() == 0


def test_cannot_wishlist_own_collection(api_client):
    # Arrange
    owner = create_user("owner@example.com", "owner")
    col = create_collection(owner)

    api_client.force_authenticate(owner)
    url = "/users/me/wishlist/"

    payload = {"kind": "collection", "collection_id": str(col.id)}

    # Act
    res = api_client.post(url, payload, format="json")

    # Assert
    assert res.status_code == 400
    assert WishList.objects.count() == 0


def test_cannot_create_duplicate_item_wishlist(api_client):
    # Arrange
    user = create_user("user@example.com", "user")
    owner = create_user("owner@example.com", "owner")

    col = create_collection(owner)
    item = create_item(col)

    WishList.objects.create(
        user=user,
        kind=WishList.Kind.ITEM,
        item=item,
        title="dup",
    )

    api_client.force_authenticate(user)
    url = "/users/me/wishlist/"

    payload = {"kind": "item", "item_id": str(item.id)}

    # Act
    res = api_client.post(url, payload, format="json")

    # Assert
    assert res.status_code == 400
    assert WishList.objects.count() == 1


def test_delete_wishlist_by_owner(api_client):
    # Arrange
    user = create_user("user@example.com", "user")
    other = create_user("other@example.com", "other")

    col = create_collection(other)
    item = create_item(col)

    fav = WishList.objects.create(
        user=user,
        kind=WishList.Kind.ITEM,
        item=item,
        title="del",
    )

    api_client.force_authenticate(user)
    url = f"/users/wishlist/{str(fav.id)}/"

    # Act
    res = api_client.delete(url)

    # Assert
    assert res.status_code == 204
    assert WishList.objects.count() == 0


def test_cannot_delete_wishlist_of_another_user(api_client):
    # Arrange
    user = create_user("user@example.com", "user")
    other = create_user("other@example.com", "other")

    col = create_collection(other)
    item = create_item(col)

    fav = WishList.objects.create(
        user=other,
        kind=WishList.Kind.ITEM,
        item=item,
        title="other_fav",
    )

    api_client.force_authenticate(user)
    url = f"/users/wishlist/{str(fav.id)}/"

    # Act
    res = api_client.delete(url)

    # Assert
    assert res.status_code == 403
    assert WishList.objects.filter(pk=fav.id).exists()
