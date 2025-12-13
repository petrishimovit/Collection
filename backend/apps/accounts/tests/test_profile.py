import pytest

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


def test_user_profile_auto_create():
    # Arrange / Act
    u = User.objects.create_user(email="a@a.com", display_name="A", password="12345")

    # Assert
    assert u.display_name == "A"
    assert u.profile.bio == ""
    assert u.profile.collection_focus == ""


def test_user_cannot_update_other_user_profile(auth_client):
    # Arrange: другой пользователь
    u = User.objects.create_user(email="a@a.com", display_name="A", password="12345")

    # Act
    response = auth_client.put(
        f"/users/{u.id}/profile/",
        {
            "display_name": "New Petr",
            "profile": {
                "bio": "Updated",
                "website": "https://example.com",
            },
        },
        format="json",
    )

    # Assert
    assert response.status_code == 403


def test_user_update_profile(auth_client):
    # Arrange
    me = auth_client.get("/users/me/").data

    # Act
    response = auth_client.put(
        f"/users/{me['id']}/profile/",
        {
            "display_name": "New Petr",
            "profile": {"bio": "Updated", "website": "https://example.com"},
        },
        format="json",
    )

    # Assert
    assert response.status_code == 200
