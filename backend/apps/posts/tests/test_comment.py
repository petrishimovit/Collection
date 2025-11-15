import pytest
from rest_framework.exceptions import PermissionDenied

from apps.accounts.models import User
from apps.posts.models import Post, Comment, CommentReaction
from apps.posts.services.post import PostService
from apps.posts.services.comment import CommentService

pytestmark = pytest.mark.django_db


def test_comment_str_and_reaction_properties():
    # Arrange
    u1 = User.objects.create_user("a@a.com", display_name="A", password="12345")
    u2 = User.objects.create_user("b@b.com", display_name="B", password="12345")
    post = Post.objects.create(author=u1, title="T", body="b")
    comment = Comment.objects.create(post=post, author=u1, body="hi")

    CommentReaction.objects.create(comment=comment, user=u1, type=CommentReaction.LIKE)
    CommentReaction.objects.create(comment=comment, user=u2, type=CommentReaction.DISLIKE)

    # Assert
    assert f"Comment #{comment.pk}" in str(comment)
    assert comment.likes_count == 1
    assert comment.dislikes_count == 1


def test_post_service_create_and_delete_comment():
    # Arrange
    user = User.objects.create_user("a@a.com", display_name="A", password="12345")
    post = Post.objects.create(author=user, title="T", body="b")

    # Act
    comment = PostService.create_comment(post=post, user=user, body="hello")

    # Assert
    assert comment.post_id == post.id
    assert comment.author_id == user.id
    assert comment.body == "hello"

    # Act 2: delete
    PostService.delete_comment(post=post, user=user, comment_id=comment.id)

    # Assert 2
    assert Comment.objects.count() == 0


def test_post_service_delete_comment_wrong_user_forbidden():
    # Arrange
    author = User.objects.create_user("a@a.com", display_name="A", password="12345")
    other = User.objects.create_user("b@b.com", display_name="B", password="12345")
    post = Post.objects.create(author=author, title="T", body="b")
    comment = Comment.objects.create(post=post, author=author, body="hi")

    # Act / Assert
    with pytest.raises(PermissionDenied):
        PostService.delete_comment(post=post, user=other, comment_id=comment.id)


def test_comment_service_toggle_reaction_cycle():
    # Arrange
    user = User.objects.create_user("a@a.com", display_name="A", password="12345")
    post = Post.objects.create(author=user, title="T", body="b")
    comment = Comment.objects.create(post=post, author=user, body="hi")

    # Act
    d1 = CommentService.toggle_reaction(comment=comment, user=user, reaction_type="like")
    d2 = CommentService.toggle_reaction(comment=comment, user=user, reaction_type="dislike")
    d3 = CommentService.toggle_reaction(comment=comment, user=user, reaction_type="dislike")

    # Assert
    assert d1["status"] == "added"
    assert d2["status"] == "changed"
    assert d3["status"] == "removed"
