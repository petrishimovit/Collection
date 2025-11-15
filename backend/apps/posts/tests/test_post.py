import pytest

from apps.accounts.models import User
from apps.posts.models import Post, PostReaction, PostImage
from apps.posts.services.post import PostService

pytestmark = pytest.mark.django_db


def test_post_str_returns_title_or_fallback():
    # Arrange
    user = User.objects.create_user("a@a.com", display_name="A", password="12345")
    post_with_title = Post.objects.create(author=user, title="Hello", body="b")
    post_no_title = Post.objects.create(author=user, title="", body="b")

    # Assert
    assert str(post_with_title) == "Hello"
    assert str(post_no_title).startswith("Post #")


def test_post_reaction_counts_properties():
    # Arrange
    u1 = User.objects.create_user("a@a.com", display_name="A", password="12345")
    u2 = User.objects.create_user("b@b.com", display_name="B", password="12345")
    post = Post.objects.create(author=u1, title="T", body="b")

    PostReaction.objects.create(post=post, user=u1, type=PostReaction.LIKE)
    PostReaction.objects.create(post=post, user=u2, type=PostReaction.DISLIKE)

    # Assert
    assert post.likes_count == 1
    assert post.dislikes_count == 1


def test_post_service_toggle_reaction_add_change_remove():
    # Arrange
    user = User.objects.create_user("a@a.com", display_name="A", password="12345")
    post = Post.objects.create(author=user, title="T", body="b")

    # Act
    data1 = PostService.toggle_reaction(post=post, user=user, reaction_type="like")
    data2 = PostService.toggle_reaction(post=post, user=user, reaction_type="dislike")
    data3 = PostService.toggle_reaction(post=post, user=user, reaction_type="dislike")

    # Assert
    assert data1["status"] == "added"
    assert data1["likes"] == 1
    assert data1["dislikes"] == 0

    assert data2["status"] == "changed"
    assert data2["likes"] == 0
    assert data2["dislikes"] == 1

    assert data3["status"] == "removed"
    assert data3["likes"] == 0
    assert data3["dislikes"] == 0


