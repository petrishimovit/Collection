import pytest
from apps.accounts.models import User
from apps.accounts.services.user import UserService


@pytest.mark.django_db
def test_user_register_and_login_with_jwt(api_client):
    email = "user@example.com"
    password = "stringst"


    register_response = api_client.post(
        "/auth/register/",
        {
            "email": email,
            "display_name": "TestUser",
            "password": password,
        },
        format="json"
    )
    assert register_response.status_code in (200, 201), register_response.content
    assert User.objects.filter(email=email).exists()


    token_response = api_client.post(
        "/auth/token/",
        {"email": email, "password": password},
        format="json"
    )
    assert token_response.status_code == 200, token_response.content
    assert "access" in token_response.data
    assert "refresh" in token_response.data

    access = token_response.data["access"]

    me_response = api_client.get(
        "/users/me/",
        HTTP_AUTHORIZATION=f"Bearer {access}"
    )


    assert me_response.data["display_name"] == "TestUser"
    

    