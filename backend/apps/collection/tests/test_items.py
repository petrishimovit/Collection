import pytest
from django.contrib.auth import get_user_model

from apps.accounts.models import Follow
from apps.collection.models import Collection, Item

pytestmark = pytest.mark.django_db

ITEM_LIST_URL = "/items/"


def create_user(email: str, display_name: str):
    User = get_user_model()
    return User.objects.create_user(
        email=email,
        display_name=display_name,
        password="12345",
    )


def create_collection(owner, name="My collection", privacy=Collection.PRIVACY_PUBLIC, **kwargs):

    defaults = {
        "description": "Test collection",
        "privacy": privacy,
    }
    defaults.update(kwargs)
    return Collection.objects.create(owner=owner, name=name, **defaults)


def create_item(collection, name="My item", privacy=Item.PRIVACY_PUBLIC, **kwargs):

    defaults = {
        "description": "Test item",
        "privacy": privacy,
        "purchase_price": 100,
        "current_value": 150,
        "currency": "USD",
        "extra": {"secret_tag": "SECRET", "visible_tag": "VISIBLE"},
        "hidden_fields": ["purchase_price", "current_value", "secret_tag"],
    }
    defaults.update(kwargs)
    return Item.objects.create(collection=collection, name=name, **defaults)


def test_item_list_anonymous_sees_only_public_items_in_public_collections(api_client, user):
    # Arrange
    owner = user
    col_public = create_collection(owner, "Public", Collection.PRIVACY_PUBLIC)
    col_private = create_collection(owner, "Private", Collection.PRIVACY_PRIVATE)

    i_public_public = create_item(col_public, "I_public_public", Item.PRIVACY_PUBLIC)
    create_item(col_public, "I_public_follow", Item.PRIVACY_FOLLOWING)
    create_item(col_public, "I_public_private", Item.PRIVACY_PRIVATE)
    create_item(col_private, "I_private_public", Item.PRIVACY_PUBLIC)

    # Act
    response = api_client.get(ITEM_LIST_URL)

    # Assert
    assert response.status_code == 200
    names = {i["name"] for i in response.data["results"]}
    assert i_public_public.name in names
    assert "I_public_follow" not in names
    assert "I_public_private" not in names
    assert "I_private_public" not in names


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
    other = create_user("other@example.com", "Other")

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


def test_item_list_authenticated_user_followed_by_owner_sees_following_only_items(api_client):
    # Arrange
    owner = create_user("owner@example.com", "owner")
    viewer = create_user("viewer@example.com", "viewer")

    col_public = create_collection(owner, "Public", Collection.PRIVACY_PUBLIC)

    i_public = create_item(col_public, "I_public", Item.PRIVACY_PUBLIC)
    i_following = create_item(col_public, "I_following", Item.PRIVACY_FOLLOWING)
    i_private = create_item(col_public, "I_private", Item.PRIVACY_PRIVATE)

    Follow.objects.create(follower=owner, following=viewer)

    api_client.force_authenticate(viewer)

    # Act
    response = api_client.get(ITEM_LIST_URL)

    # Assert
    assert response.status_code == 200
    names = {i["name"] for i in response.data["results"]}

    assert i_public.name in names
    assert i_following.name in names
    assert i_private.name not in names


def test_item_list_authenticated_user_not_followed_by_owner_sees_only_public(api_client):
    # Arrange
    owner = create_user("owner@example.com", "owner")
    viewer = create_user("viewer@example.com", "viewer")

    col_public = create_collection(owner, "Public", Collection.PRIVACY_PUBLIC)

    i_public = create_item(col_public, "I_public", Item.PRIVACY_PUBLIC)
    create_item(col_public, "I_following", Item.PRIVACY_FOLLOWING)

    api_client.force_authenticate(viewer)

    # Act
    response = api_client.get(ITEM_LIST_URL)

    # Assert
    assert response.status_code == 200
    names = {i["name"] for i in response.data["results"]}

    assert i_public.name in names
    assert "I_following" not in names


def test_item_list_respects_following_collection_visibility(api_client):
    # Arrange
    owner = create_user("owner@example.com", "owner")
    viewer = create_user("viewer@example.com", "viewer")

    col_following = create_collection(owner, "Following", Collection.PRIVACY_FOLLOWING)

    i_public = create_item(col_following, "I_public", Item.PRIVACY_PUBLIC)
    i_following = create_item(col_following, "I_following", Item.PRIVACY_FOLLOWING)
    i_private = create_item(col_following, "I_private", Item.PRIVACY_PRIVATE)

    api_client.force_authenticate(viewer)

    # Act
    res_no_follow = api_client.get(ITEM_LIST_URL)
    names_no_follow = {i["name"] for i in res_no_follow.data["results"]}

    # Assert
    assert i_public.name not in names_no_follow
    assert i_following.name not in names_no_follow
    assert i_private.name not in names_no_follow

    # Arrange
    Follow.objects.create(follower=owner, following=viewer)

    # Act
    res_followed = api_client.get(ITEM_LIST_URL)
    names_followed = {i["name"] for i in res_followed.data["results"]}

    # Assert
    assert i_public.name in names_followed
    assert i_following.name in names_followed
    assert i_private.name not in names_followed


def test_item_search_filters_by_name(api_client, user):
    # Arrange
    col = create_collection(user, "C1")
    create_item(col, "Super Mario", Item.PRIVACY_PUBLIC)
    create_item(col, "Zelda", Item.PRIVACY_PUBLIC)

    # Act
    response = api_client.get(f"{ITEM_LIST_URL}search/?q=mario")

    # Assert
    assert response.status_code == 200
    names = {i["name"] for i in response.data["results"]}
    assert "Super Mario" in names
    assert "Zelda" not in names


def test_item_hidden_fields_visible_for_owner(auth_client, user):

    col = create_collection(user, "C1")
    item = create_item(col, "I1")

    url = f"/items/{item.id}/"
    response = auth_client.get(url)

    assert response.status_code == 200

    data = response.data

    assert "hidden_fields" in data
    assert set(data["hidden_fields"]) == {
        "purchase_price",
        "current_value",
        "secret_tag",
    }

    assert str(data["purchase_price"]) in ("100", "100.00")
    assert str(data["current_value"]) in ("150", "150.00")

    extra = data["extra"]
    assert extra["secret_tag"] == "SECRET"
    assert extra["visible_tag"] == "VISIBLE"


def test_item_hidden_fields_masked_for_anonymous(api_client, user):

    col = create_collection(user, "C1")
    item = create_item(col, "I1")

    url = f"/items/{item.id}/"
    response = api_client.get(url)

    assert response.status_code == 200
    data = response.data

    assert "hidden_fields" not in data

    assert data.get("purchase_price") is None
    assert data.get("current_value") is None

    extra = data["extra"]

    assert "visible_tag" in extra
    assert "secret_tag" in extra


def test_item_hidden_fields_masked_for_non_owner(auth_client, user, api_client):

    owner = user
    other = get_user_model().objects.create_user(
        email="other@example.com",
        display_name="Other",
        password="12345",
    )

    col = create_collection(owner, "C1")
    item = create_item(col, "I1")

    api_client.force_authenticate(user=other)

    url = f"/items/{item.id}/"
    response = api_client.get(url)

    assert response.status_code == 200
    data = response.data

    assert "hidden_fields" not in data
    assert data.get("purchase_price") is None
    assert data.get("current_value") is None

    extra = data["extra"]
    assert "visible_tag" in extra

    assert "secret_tag" in extra


def test_item_hidden_fields_can_be_cleared_with_patch(auth_client, user):

    col = create_collection(user, "C1")
    item = create_item(col, "I1")

    url = f"/items/{item.id}/"
    payload = {"hidden_fields": []}
    response = auth_client.patch(url, payload, format="json")

    assert response.status_code == 200
    assert response.data["hidden_fields"] == []

    from rest_framework.test import APIClient

    anon_client = APIClient()
    response_anon = anon_client.get(url)
    assert response_anon.status_code == 200

    data = response_anon.data

    assert "hidden_fields" not in data
