import pytest

from apps.accounts.models import User
from apps.collection.models import Collection, Item

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


def test_collection_is_favorite_default_false():
    # Arrange
    owner = create_user("owner@example.com", "owner")

    # Act
    col = create_collection(owner, "Col")

    # Assert
    assert col.is_favorite is False


def test_item_is_favorite_default_false():
    # Arrange
    owner = create_user("owner@example.com", "owner")
    col = create_collection(owner, "Col")

    # Act
    item = create_item(col, "Item")

    # Assert
    assert item.is_favorite is False


def test_collection_is_favorite_cannot_be_changed_via_api(api_client):
    """
    At the moment collection partial updates are not allowed (update returns 405),
    so is_favorite cannot be toggled via API.
    """
    # Arrange
    owner = create_user("owner@example.com", "owner")
    col = create_collection(owner, "Fav Col")

    api_client.force_authenticate(owner)
    url = f"/collections/{col.id}/"

    payload = {"is_favorite": True}

    # Act
    res = api_client.patch(url, payload, format="json")

    # Assert
    assert res.status_code == 405
    col.refresh_from_db()
    assert col.is_favorite is False


def test_collection_is_favorite_cannot_be_changed_by_non_owner(api_client):
    """
    Non-owners also cannot change is_favorite — they receive the same 405
    because collection updates are disabled at the endpoint level.
    """
    # Arrange
    owner = create_user("owner@example.com", "owner")
    other = create_user("other@example.com", "other")
    col = create_collection(owner, "Col")

    api_client.force_authenticate(other)
    url = f"/collections/{col.id}/"

    payload = {"is_favorite": True}

    # Act
    res = api_client.patch(url, payload, format="json")

    # Assert
    assert res.status_code == 405
    col.refresh_from_db()
    assert col.is_favorite is False


def test_owner_can_set_item_is_favorite(api_client):
    # Arrange
    owner = create_user("owner@example.com", "owner")
    col = create_collection(owner, "Col")
    item = create_item(col, "Item A")

    api_client.force_authenticate(owner)
    url = f"/items/{item.id}/"

    payload = {"is_favorite": True}

    # Act
    res = api_client.patch(url, payload, format="json")

    # Assert
    assert res.status_code == 200
    item.refresh_from_db()
    assert item.is_favorite is True
    assert res.data["is_favorite"] is True


def test_non_owner_cannot_set_item_is_favorite(api_client):
    # Arrange
    owner = create_user("owner@example.com", "owner")
    other = create_user("other@example.com", "other")
    col = create_collection(owner, "Col")
    item = create_item(col, "Item A")

    api_client.force_authenticate(other)
    url = f"/items/{item.id}/"

    payload = {"is_favorite": True}

    # Act
    res = api_client.patch(url, payload, format="json")

    # Assert
    assert res.status_code in (403, 404)
    item.refresh_from_db()
    assert item.is_favorite is False


def test_items_list_filter_is_favorite(api_client):
    # Arrange
    owner = create_user("owner@example.com", "owner")
    col = create_collection(owner, "Col")

    item1 = create_item(col, "I1")
    item2 = create_item(col, "I2")
    item3 = create_item(col, "I3")

    Item.objects.filter(pk=item1.pk).update(is_favorite=True)
    Item.objects.filter(pk=item2.pk).update(is_favorite=False)
    Item.objects.filter(pk=item3.pk).update(is_favorite=True)

    api_client.force_authenticate(owner)
    url = "/items/"

    # Act
    res_all = api_client.get(url)
    res_fav = api_client.get(url, {"is_favorite": "true"})
    res_not_fav = api_client.get(url, {"is_favorite": "false"})

    # Assert
    assert res_all.status_code == 200
    ids_all = {i["id"] for i in res_all.data["results"]}
    assert ids_all == {str(item1.id), str(item2.id), str(item3.id)}

    assert res_fav.status_code == 200
    ids_fav = {i["id"] for i in res_fav.data["results"]}
    assert ids_fav == {str(item1.id), str(item3.id)}

    assert res_not_fav.status_code == 200
    ids_not_fav = {i["id"] for i in res_not_fav.data["results"]}
    assert ids_not_fav == {str(item2.id)}
