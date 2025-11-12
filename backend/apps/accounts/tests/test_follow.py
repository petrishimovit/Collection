import pytest
from apps.accounts.models import User, Follow
from apps.accounts.services.user import UserService

@pytest.mark.django_db
def test_user_follow():

    u1 = User.objects.create_user(email="a@a.com", display_name="A", password="12345")
    u2 = User.objects.create_user(email="b@b.com", display_name="B", password="12345")

    Follow.objects.create(follower=u1, following=u2)

    assert u1.is_following(u2)

@pytest.mark.django_db
def test_user_unfollow():
    u1 = User.objects.create_user(email="a@a.com", display_name="A", password="12345")
    u2 = User.objects.create_user(email="b@b.com", display_name="B", password="12345")

    Follow.objects.create(follower=u1, following=u2)

    u1.unfollow(u2)

    assert not u1.is_following(u2)

@pytest.mark.django_db
def test_user_follow_toggle():
    u1 = User.objects.create_user(email="a@a.com", display_name="A", password="12345")
    u2 = User.objects.create_user(email="b@b.com", display_name="B", password="12345")

    UserService.toggle_follow(actor=u1,target=u2)

    assert u1.is_following(u2)

    UserService.toggle_follow(actor=u1,target=u2)

    assert not u1.is_following(u2)


@pytest.mark.django_db
def test_user_followers_count():
    u1 = User.objects.create_user(email="a@a.com", display_name="A", password="12345")
    u2 = User.objects.create_user(email="b@b.com", display_name="B", password="12345")

    UserService.toggle_follow(actor=u1,target=u2)

    assert u1.followers_count == 0


    assert u2.followers_count == 1

    

    