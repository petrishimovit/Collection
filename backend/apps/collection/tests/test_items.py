import pytest
from django.contrib.auth import get_user_model

from apps.collection.models import Collection, Item
from apps.accounts.models import Follow

pytestmark = pytest.mark.django_db

ITEM_LIST_URL = "/items/"


def create_user(email: str, display_name: str):
    User = get_user_model()
    return User.objects.create_user(
        email=email,
        display_name=display_name,
        password="12345",
    )


def create_collection(owner, name="My collection", privacy=Collection.PRIVACY_PUBLIC):
    return Collection.objects.create(
        owner=owner,
        name=name,
        privacy=privacy,
    )


def create_item(collection, name="My item", privacy=Item.PRIVACY_PUBLIC):
    return Item.objects.create(
        collection=collection,
        name=name,
        privacy=privacy,
    )


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
    res_no_follow = api_client.get(ITEM_LIST_URL)
    names_no_follow = {i["name"] for i in res_no_follow.data["results"]}
    assert i_public.name not in names_no_follow
    assert i_following.name not in names_no_follow
    assert i_private.name not in names_no_follow


    Follow.objects.create(follower=owner, following=viewer)

    res_followed = api_client.get(ITEM_LIST_URL)
    names_followed = {i["name"] for i in res_followed.data["results"]}

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
