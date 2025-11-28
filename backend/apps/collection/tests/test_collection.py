import pytest
from django.contrib.auth import get_user_model

from apps.collection.models import Collection, Item
from apps.accounts.models import Follow

pytestmark = pytest.mark.django_db

COLLECTION_LIST_URL = "/collections/"
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


def test_collections_list_returns_only_public_for_anonymous(api_client, user):
    # Arrange
    owner = user
    public_col = create_collection(owner, "Public", Collection.PRIVACY_PUBLIC)
    private_col = create_collection(owner, "Private", Collection.PRIVACY_PRIVATE)
    following_col = create_collection(owner, "Following", Collection.PRIVACY_FOLLOWING)

    # Act
    response = api_client.get(COLLECTION_LIST_URL)

    # Assert
    assert response.status_code == 200
    ids = {c["id"] for c in response.data["results"]}  # JSON -> строки
    assert str(public_col.id) in ids
    assert str(private_col.id) not in ids
    assert str(following_col.id) not in ids


def test_collections_list_returns_only_public_for_authenticated(auth_client, user):
    # Arrange
    owner = user
    public_col = create_collection(owner, "Public", Collection.PRIVACY_PUBLIC)
    private_col = create_collection(owner, "Private", Collection.PRIVACY_PRIVATE)
    following_col = create_collection(owner, "Following", Collection.PRIVACY_FOLLOWING)

    # Act
    response = auth_client.get(COLLECTION_LIST_URL)

    # Assert
    assert response.status_code == 200
    ids = {c["id"] for c in response.data["results"]}
    assert str(public_col.id) in ids
    assert str(private_col.id) not in ids
    assert str(following_col.id) not in ids


def test_collections_retrieve_respects_privacy_and_follow(api_client):
    # Arrange
    owner = create_user("owner@example.com", "owner")
    viewer = create_user("viewer@example.com", "viewer")

    public_col = create_collection(owner, "Public", Collection.PRIVACY_PUBLIC)
    following_col = create_collection(owner, "Following", Collection.PRIVACY_FOLLOWING)
    private_col = create_collection(owner, "Private", Collection.PRIVACY_PRIVATE)

 
    # Act
    res_public_anon = api_client.get(f"{COLLECTION_LIST_URL}{public_col.id}/")
    res_following_anon = api_client.get(f"{COLLECTION_LIST_URL}{following_col.id}/")
    res_private_anon = api_client.get(f"{COLLECTION_LIST_URL}{private_col.id}/")

    # Assert
    assert res_public_anon.status_code == 200
    assert res_following_anon.status_code == 404
    assert res_private_anon.status_code == 404

 
    api_client.force_authenticate(viewer)
    res_public_viewer = api_client.get(f"{COLLECTION_LIST_URL}{public_col.id}/")
    res_following_viewer = api_client.get(f"{COLLECTION_LIST_URL}{following_col.id}/")
    res_private_viewer = api_client.get(f"{COLLECTION_LIST_URL}{private_col.id}/")

    assert res_public_viewer.status_code == 200
    assert res_following_viewer.status_code == 404
    assert res_private_viewer.status_code == 404


    Follow.objects.create(follower=owner, following=viewer)

    res_following_viewer2 = api_client.get(f"{COLLECTION_LIST_URL}{following_col.id}/")
    res_private_viewer2 = api_client.get(f"{COLLECTION_LIST_URL}{private_col.id}/")

    assert res_following_viewer2.status_code == 200
    assert res_private_viewer2.status_code == 404


    api_client.force_authenticate(owner)
    res_public_owner = api_client.get(f"{COLLECTION_LIST_URL}{public_col.id}/")
    res_following_owner = api_client.get(f"{COLLECTION_LIST_URL}{following_col.id}/")
    res_private_owner = api_client.get(f"{COLLECTION_LIST_URL}{private_col.id}/")

    assert res_public_owner.status_code == 200
    assert res_following_owner.status_code == 200
    assert res_private_owner.status_code == 200


def test_collections_feed_requires_auth(api_client):
    # Act
    response = api_client.get(f"{COLLECTION_LIST_URL}feed/")

    # Assert
    assert response.status_code in (401, 403)


def test_collections_feed_visibility_with_follow_and_mutual(api_client):
    # Arrange
    user = create_user("user@example.com", "user")
    owner = create_user("owner@example.com", "owner")

    public_col = create_collection(owner, "Public", Collection.PRIVACY_PUBLIC)
    following_col = create_collection(owner, "Following", Collection.PRIVACY_FOLLOWING)
    private_col = create_collection(owner, "Private", Collection.PRIVACY_PRIVATE)

    api_client.force_authenticate(user)


    # Act
    res_no_follow = api_client.get(f"{COLLECTION_LIST_URL}feed/")
    # Assert
    assert res_no_follow.status_code == 200
    assert res_no_follow.data["count"] == 0


    Follow.objects.create(follower=user, following=owner)

    res_one_way = api_client.get(f"{COLLECTION_LIST_URL}feed/")
    ids = {c["id"] for c in res_one_way.data["results"]}
    assert str(public_col.id) in ids
    assert str(following_col.id) not in ids
    assert str(private_col.id) not in ids

    Follow.objects.create(follower=owner, following=user)

    res_mutual = api_client.get(f"{COLLECTION_LIST_URL}feed/")
    ids2 = {c["id"] for c in res_mutual.data["results"]}
    assert str(public_col.id) in ids2
    assert str(following_col.id) in ids2
    assert str(private_col.id) not in ids2


def test_collections_create_requires_auth(api_client, user):
    # Arrange
    payload = {"name": "New collection"}

    # Act
    response = api_client.post(COLLECTION_LIST_URL, payload, format="json")

    # Assert
    assert response.status_code in (401, 403)
    assert not Collection.objects.filter(name="New collection").exists()


def test_collections_create_ok(auth_client, user):
    # Arrange
    payload = {
        "name": "My collection",
        "privacy": Collection.PRIVACY_FOLLOWING,
        "description": "Test desc",
    }

    # Act
    response = auth_client.post(COLLECTION_LIST_URL, payload, format="json")

    # Assert
    assert response.status_code == 201
    col = Collection.objects.get(id=response.data["id"])
    assert col.owner == user
    assert col.name == "My collection"
    assert col.privacy == Collection.PRIVACY_FOLLOWING


def test_collections_partial_update_only_owner_can_edit(api_client):
    # Arrange
    owner = create_user("owner@example.com", "owner")
    other = create_user("other@example.com", "other")

    col = create_collection(owner, "Old name", Collection.PRIVACY_PUBLIC)


    api_client.force_authenticate(other)
    res_forbidden = api_client.patch(
        f"{COLLECTION_LIST_URL}{col.id}/",
        {"name": "Hacked"},
        format="json",
    )

    # Assert

    assert res_forbidden.status_code in (403, 404, 405)
    col.refresh_from_db()
    assert col.name == "Old name"

   
    api_client.force_authenticate(owner)
    res_ok = api_client.patch(
        f"{COLLECTION_LIST_URL}{col.id}/",
        {"name": "New name"},
        format="json",
    )

    
    col.refresh_from_db()
    


def test_collection_items_endpoint_respects_visibility(api_client):
    # Arrange
    owner = create_user("owner@example.com", "owner")
    viewer = create_user("viewer@example.com", "viewer")

    col_public = create_collection(owner, "Public", Collection.PRIVACY_PUBLIC)
    col_following = create_collection(owner, "Following", Collection.PRIVACY_FOLLOWING)

    i_public = create_item(col_public, "I_public", Item.PRIVACY_PUBLIC)
    i_following_public = create_item(col_following, "I_follow_pub", Item.PRIVACY_PUBLIC)
    i_following_only = create_item(col_following, "I_follow_only", Item.PRIVACY_FOLLOWING)

 
    api_client.force_authenticate(viewer)

    res_public = api_client.get(f"{COLLECTION_LIST_URL}{col_public.id}/items/")
    res_following = api_client.get(f"{COLLECTION_LIST_URL}{col_following.id}/items/")

   
    assert res_public.status_code == 200
    names_public = {i["name"] for i in res_public.data["results"]}
    assert i_public.name in names_public

 
    assert res_following.status_code == 200
    assert res_following.data["count"] == 0

    
    Follow.objects.create(follower=owner, following=viewer)

    res_following2 = api_client.get(f"{COLLECTION_LIST_URL}{col_following.id}/items/")
    names_following2 = {i["name"] for i in res_following2.data["results"]}

    assert i_following_public.name in names_following2
    assert i_following_only.name in names_following2
