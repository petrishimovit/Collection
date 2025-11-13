import pytest
import factory
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.accounts.models import Follow

User = get_user_model()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@ex.com")
    display_name = factory.Sequence(lambda n: f"User {n}")
    password = factory.PostGenerationMethodCall("set_password", "pass12345")

@pytest.fixture
def user_factory():
    return UserFactory

@pytest.fixture
def user(db, user_factory):
    return user_factory()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="user@example.com",
        display_name="User",
        password="12345"
    )

@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(
        email="admin@example.com",
        display_name="Admin",
        password="12345"
    )


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client

@pytest.fixture
def superuser_client(superuser):
    client = APIClient()
    client.force_authenticate(user=superuser)
    return client