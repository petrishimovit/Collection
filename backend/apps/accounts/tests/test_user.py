import pytest

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


def test_user_register_and_cannot_login_while_inactive(api_client):
    # Arrange
    email = "user@example.com"
    password = "stringst"

    # Act
    register_response = api_client.post(
        "/auth/register/",
        {
            "email": email,
            "display_name": "TestUser",
            "password": password,
        },
        format="json",
    )

    # Assert
    assert register_response.status_code in (200, 201), register_response.content
    assert User.objects.filter(email=email).exists()

    user = User.objects.get(email=email)

    assert user.is_active is False

    # Act
    token_response = api_client.post(
        "/auth/token/",
        {"email": email, "password": password},
        format="json",
    )

    # Assert
    assert token_response.status_code == 401

    assert token_response.data["detail"] == "No active account found with the given credentials"
    assert getattr(token_response.data["detail"], "code", None) == "no_active_account"
