import pytest
from apps.accounts.models import User, Follow

@pytest.mark.django_db
def test_user_follow_manual():
    
    u1 = User.objects.create_user(email="a@a.com", display_name="A", password="12345")
    u2 = User.objects.create_user(email="b@b.com", display_name="B", password="12345")

    Follow.objects.create(follower=u1, following=u2)

    assert u1.is_following(u2)
