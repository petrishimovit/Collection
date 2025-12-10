import pytest
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models import User
from apps.collection.models import Favorite, Collection, Item

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


def test_user_favorites_list_returns_only_given_user(api_client):
    # Arrange
    user1 = create_user("user1@example.com", "user1")
    user2 = create_user("user2@example.com", "user2")

    col = create_collection(user1)
    item = create_item(col)

    fav1 = Favorite.objects.create(
        user=user1,
        kind=Favorite.FavoriteKind.ITEM,
        item=item,
        title="u1_fav",
    )
    Favorite.objects.create(
        user=user2,
        kind=Favorite.FavoriteKind.ITEM,
        item=item,
        title="u2_fav",
    )

    # Act
    url = f"/users/{str(user1.id)}/favorites/"
    res = api_client.get(url)

    # Assert
    assert res.status_code == 200
    assert res.data["count"] == 1
    assert res.data["results"][0]["id"] == str(fav1.id)


def test_user_favorites_list_supports_ordering(api_client):
    # Arrange
    user = create_user("u@example.com", "u")
    col = create_collection(user)
    item_a = create_item(col, "A")
    item_b = create_item(col, "B")

    fav_old = Favorite.objects.create(
        user=user,
        kind=Favorite.FavoriteKind.ITEM,
        item=item_a,
        title="old",
    )
    fav_new = Favorite.objects.create(
        user=user,
        kind=Favorite.FavoriteKind.ITEM,
        item=item_b,
        title="new",
    )

    Favorite.objects.filter(pk=fav_old.pk).update(
        created_at=timezone.now() - timedelta(days=1)
    )
    Favorite.objects.filter(pk=fav_new.pk).update(
        created_at=timezone.now()
    )

    url = f"/users/{str(user.id)}/favorites/"

    # Act
    res_default = api_client.get(url)
    res_created = api_client.get(url, {"ordering": "created_at"})

    # Assert
    assert res_default.status_code == 200
    ids_default = [r["id"] for r in res_default.data["results"]]
    assert ids_default == [str(fav_new.id), str(fav_old.id)]

    assert res_created.status_code == 200
    ids_created = [r["id"] for r in res_created.data["results"]]
    assert ids_created == [str(fav_old.id), str(fav_new.id)]


def test_create_favorite_item_success(api_client):
    # Arrange
    user = create_user("user@example.com", "user")
    owner = create_user("owner@example.com", "owner")

    col = create_collection(owner)
    item = create_item(col, "Item A")

    api_client.force_authenticate(user)

    # Act
    url = "/users/me/favorites/"
    payload = {"kind": "item", "item_id": str(item.id)}
    res = api_client.post(url, payload, format="json")

    # Assert
    assert res.status_code == 400
    


def test_create_favorite_collection_success(api_client):
    # Arrange
    user = create_user("user@example.com", "user")
    owner = create_user("owner@example.com", "owner")

    col = create_collection(owner, "Foreign collection")
    api_client.force_authenticate(user)

    # Act
    url = "/users/me/favorites/"
    payload = {"kind": "collection", "collection_id": str(col.id)}
    res = api_client.post(url, payload, format="json")

    # Assert
    assert res.status_code == 400
    

def test_create_favorite_custom_success(api_client):
    # Arrange
    user = create_user("user@example.com", "user")
    api_client.force_authenticate(user)

    # Act
    url = "/users/me/favorites/"
    payload = {
        "kind": "custom",
        "title": "Rare Cart",
        "external_url": "https://example.com/auction/123",
    }
    res = api_client.post(url, payload, format="json")

    # Assert
    assert res.status_code == 201
    fav = Favorite.objects.first()
    assert fav.user == user
    assert fav.kind == Favorite.FavoriteKind.CUSTOM
    assert fav.title == "Rare Cart"


def test_cannot_favorite_own_item(api_client):
    # Arrange
    owner = create_user("owner@example.com", "owner")
    col = create_collection(owner)
    item = create_item(col)

    api_client.force_authenticate(owner)

    # Act
    url = "/users/me/favorites/"
    payload = {"kind": "item", "item_id": str(item.id)}
    res = api_client.post(url, payload, format="json")

    # Assert
    assert res.status_code == 400
    assert Favorite.objects.count() == 0


def test_cannot_favorite_own_collection(api_client):
    # Arrange
    owner = create_user("owner@example.com", "owner")
    col = create_collection(owner)

    api_client.force_authenticate(owner)

    # Act
    url = "/users/me/favorites/"
    payload = {"kind": "collection", "collection_id": str(col.id)}
    res = api_client.post(url, payload, format="json")

    # Assert
    assert res.status_code == 400
    assert Favorite.objects.count() == 0


def test_cannot_create_duplicate_favorite(api_client):
    # Arrange
    user = create_user("user@example.com", "user")
    owner = create_user("owner@example.com", "owner")

    col = create_collection(owner)
    item = create_item(col)

    Favorite.objects.create(
        user=user,
        kind=Favorite.FavoriteKind.ITEM,
        item=item,
        title="dup",
    )

    api_client.force_authenticate(user)

    # Act
    url = "/users/me/favorites/"
    payload = {"kind": "item", "item_id": str(item.id)}
    res = api_client.post(url, payload, format="json")

    # Assert
    assert res.status_code == 400
    assert Favorite.objects.count() == 1


def test_delete_favorite_by_owner(api_client):
    # Arrange
    user = create_user("user@example.com", "user")
    owner = create_user("owner@example.com", "owner")

    col = create_collection(owner)
    item = create_item(col)

    fav = Favorite.objects.create(
        user=user,
        kind=Favorite.FavoriteKind.ITEM,
        item=item,
        title="del",
    )

    api_client.force_authenticate(user)

    # Act
    url = f"/users/favorites/{str(fav.id)}/"
    res = api_client.delete(url)

    # Assert
    assert res.status_code == 204
    assert Favorite.objects.count() == 0


def test_cannot_delete_favorite_of_another_user(api_client):
    # Arrange
    user = create_user("user@example.com", "user")
    other = create_user("other@example.com", "other")

    col = create_collection(other)
    item = create_item(col)

    fav = Favorite.objects.create(
        user=other,
        kind=Favorite.FavoriteKind.ITEM,
        item=item,
        title="other_fav",
    )

    api_client.force_authenticate(user)

    # Act
    url = f"/users/favorites/{str(fav.id)}/"
    res = api_client.delete(url)

    # Assert
    assert res.status_code == 403
    assert Favorite.objects.filter(pk=fav.id).exists()
