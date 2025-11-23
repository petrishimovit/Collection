import pytest

from apps.accounts.models import User
from apps.posts.models import Post, Comment, PostReaction, CommentReaction

pytestmark = pytest.mark.django_db


def test_post_react_like(api_client):
    # Arrange
    user = User.objects.create_user("a@a.com", display_name="A", password="12345")
    post = Post.objects.create(author=user, text="post text")

    api_client.force_authenticate(user)

    # Act
    res = api_client.post(f"/posts/{post.id}/react/", {"type": "like"}, format="json")

    # Assert
    assert res.status_code == 200
    assert res.data["status"] == "added"
    assert PostReaction.objects.filter(post=post, user=user, type="like").exists()


def test_post_react_toggle_remove(api_client):
    # Arrange
    user = User.objects.create_user("a@a.com", display_name="A", password="12345")
    post = Post.objects.create(author=user, text="post text")

    api_client.force_authenticate(user)
    api_client.post(f"/posts/{post.id}/react/", {"type": "like"}, format="json")

    # Act
    res = api_client.post(f"/posts/{post.id}/react/", {"type": "like"}, format="json")

    # Assert
    assert res.status_code == 200
    assert res.data["status"] == "removed"
    assert not PostReaction.objects.filter(post=post, user=user).exists()


def test_comment_react_like(api_client):
    # Arrange
    user = User.objects.create_user("a@a.com", display_name="A", password="12345")
    post = Post.objects.create(author=user, text="post text")
    comment = Comment.objects.create(post=post, author=user, text="hi")

    api_client.force_authenticate(user)

    # Act
    res = api_client.post(f"/comments/{comment.id}/react/", {"type": "like"}, format="json")

    # Assert
    assert res.status_code == 200
    assert res.data["status"] == "added"
    assert CommentReaction.objects.filter(comment=comment, user=user, type="like").exists()


def test_comment_react_toggle_change(api_client):
    # Arrange
    user = User.objects.create_user("a@a.com", display_name="A", password="12345")
    post = Post.objects.create(author=user, text="post text")
    comment = Comment.objects.create(post=post, author=user, text="hi")

    api_client.force_authenticate(user)
    api_client.post(f"/comments/{comment.id}/react/", {"type": "like"}, format="json")

    # Act
    res = api_client.post(f"/comments/{comment.id}/react/", {"type": "dislike"}, format="json")

    # Assert
    assert res.status_code == 200
    assert res.data["status"] == "changed"
    assert CommentReaction.objects.filter(comment=comment, user=user, type="dislike").exists()
