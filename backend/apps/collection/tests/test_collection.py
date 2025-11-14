import pytest
from apps.collection.models import Collection, Item

pytestmark = pytest.mark.django_db

ITEM_LIST_URL = "/items/"


def create_collection(owner, name="My collection"):
    return Collection.objects.create(owner=owner, name=name)


def create_item(collection, name="My item"):
    return Item.objects.create(collection=collection, name=name)


def test_item_list_anonymous_ok(api_client, user):
    # Arrange
    col = create_collection(user, "C1")
    create_item(col, "I1")
    create_item(col, "I2")

    # Act
    response = api_client.get(ITEM_LIST_URL)

    # Assert
    assert response.status_code == 200
    names = {i["name"] for i in response.data["results"]}
    assert {"I1", "I2"}.issubset(names)


def test_item_create_requires_auth(api_client, user):
    # Arrange
    col = create_collection(user, "C1")
    payload = {"collection": col.id, "name": "New item"}

    # Act
    response = api_client.post(ITEM_LIST_URL, payload, format="json")

    # Assert
    assert response.status_code in (401, 403)


def test_item_create_only_in_own_collection(auth_client, user):
    # Arrange
    from django.contrib.auth import get_user_model
    other = get_user_model().objects.create_user(
        email="other@example.com",
        display_name="Other",
        password="12345",
    )

    own_col = create_collection(user, "Own col")
    other_col = create_collection(other, "Other col")

    payload = {"collection": other_col.id, "name": "Should fail"}

    # Act
    response = auth_client.post(ITEM_LIST_URL, payload, format="json")

    # Assert
    assert response.status_code == 403
    assert not Item.objects.filter(name="Should fail").exists()


def test_item_create_in_own_collection_ok(auth_client, user):
    # Arrange
    col = create_collection(user, "Own col")
    payload = {"collection": col.id, "name": "My item"}

    # Act
    response = auth_client.post(ITEM_LIST_URL, payload, format="json")

    # Assert
    assert response.status_code == 201
    item = Item.objects.get(id=response.data["id"])
    assert item.collection == col
    assert item.collection.owner == user
