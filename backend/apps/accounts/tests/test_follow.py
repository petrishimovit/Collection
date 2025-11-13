import pytest

from apps.accounts.models import User, Follow
from apps.accounts.services.user import UserService


pytestmark = pytest.mark.django_db


def test_user_follow():
    # Arrange
    u1 = User.objects.create_user(email="a@a.com", display_name="A", password="12345")
    u2 = User.objects.create_user(email="b@b.com", display_name="B", password="12345")

    # Act
    Follow.objects.create(follower=u1, following=u2)

    # Assert
    assert u1.is_following(u2)


def test_user_unfollow():
    # Arrange
    u1 = User.objects.create_user(email="a@a.com", display_name="A", password="12345")
    u2 = User.objects.create_user(email="b@b.com", display_name="B", password="12345")
    Follow.objects.create(follower=u1, following=u2)

    # Act
    u1.unfollow(u2)

    # Assert
    assert not u1.is_following(u2)


def test_user_follow_toggle():
    # Arrange
    u1 = User.objects.create_user(email="a@a.com", display_name="A", password="12345")
    u2 = User.objects.create_user(email="b@b.com", display_name="B", password="12345")

    # Act
    UserService.toggle_follow(actor=u1, target=u2)
    # Assert
    assert u1.is_following(u2)

    # Act again (unfollow)
    UserService.toggle_follow(actor=u1, target=u2)
    # Assert
    assert not u1.is_following(u2)


def test_user_followers_count():
    # Arrange
    u1 = User.objects.create_user(email="a@a.com", display_name="A", password="12345")
    u2 = User.objects.create_user(email="b@b.com", display_name="B", password="12345")

    # Act
    UserService.toggle_follow(actor=u1, target=u2)

    # Assert
    assert u1.followers_count == 0
    assert u2.followers_count == 1


def test_follow_api(api_client):
    # Arrange
    u1 = User.objects.create_user(email="a@a.com", display_name="A", password="12345")
    u2 = User.objects.create_user(email="b@b.com", display_name="B", password="12345")
    UserService.toggle_follow(actor=u1, target=u2)

    # Act
    response_1 = api_client.get(f"/users/{u1.id}/following/")
    response_2 = api_client.get(f"/users/{u2.id}/following/")

    # Assert
    assert response_1.status_code == 200
    assert response_1.data["results"][0]["id"] == str(u2.id)

    assert response_2.status_code == 200
    assert response_2.data["results"] == []
