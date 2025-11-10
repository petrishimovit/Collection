import pytest
import factory
from django.contrib.auth import get_user_model
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
    from rest_framework.test import APIClient
    return APIClient()
