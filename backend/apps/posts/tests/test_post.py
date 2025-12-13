import pytest

from apps.accounts.models import User
from apps.posts.models import Comment, Post, PostReaction
from apps.posts.services.post import PostService

pytestmark = pytest.mark.django_db


def test_post_str_has_id_or_label():
    # Arrange
    user = User.objects.create_user("a@a.com", display_name="A", password="12345")
    post = Post.objects.create(author=user, text="Hello world")

    # Assert
    assert str(post)


def test_post_reaction_counts_properties():
    # Arrange
    u1 = User.objects.create_user("a@a.com", display_name="A", password="12345")
    u2 = User.objects.create_user("b@b.com", display_name="B", password="12345")
    post = Post.objects.create(author=u1, text="post text")

    PostReaction.objects.create(post=post, user=u1, type=PostReaction.LIKE)
    PostReaction.objects.create(post=post, user=u2, type=PostReaction.DISLIKE)

    # Assert
    assert post.likes_count == 1
    assert post.dislikes_count == 1


def test_post_service_toggle_reaction_add_change_remove():
    # Arrange
    user = User.objects.create_user("a@a.com", display_name="A", password="12345")
    post = Post.objects.create(author=user, text="post text")

    # Act
    data1 = PostService.toggle_reaction(post=post, user=user, reaction_type="like")
    data2 = PostService.toggle_reaction(post=post, user=user, reaction_type="dislike")
    data3 = PostService.toggle_reaction(post=post, user=user, reaction_type="dislike")

    # Assert
    assert data1["status"] == "added"
    assert data2["status"] == "changed"
    assert data3["status"] == "removed"


def test_posts_list(api_client, user):
    # Arrange
    Post.objects.create(author=user, text="post 1")
    Post.objects.create(author=user, text="post 2")

    # Act
    response = api_client.get("/posts/")

    # Assert
    assert response.status_code == 200
    assert len(response.data["results"]) == 2


def test_posts_retrieve(api_client, user):
    # Arrange
    post = Post.objects.create(author=user, text="detail text")
    url = f"/posts/{post.id}/"

    # Act
    response = api_client.get(url)

    # Assert
    assert response.status_code == 200
    assert response.data["id"] == str(post.id)


def test_posts_retrieve_increments_views(api_client, user):
    # Arrange
    post = Post.objects.create(author=user, text="with views", views_count=0)
    url = f"/posts/{post.id}/"

    # Act
    response = api_client.get(url)

    # Assert
    assert response.data["views_count"] == 1


def test_posts_create_requires_auth(api_client):
    # Arrange
    payload = {"text": "unauth"}

    # Act
    response = api_client.post("/posts/", data=payload, format="json")

    # Assert
    assert response.status_code in (401, 403)


def test_posts_create_success(auth_client, user):
    # Arrange
    payload = {"text": "new post"}

    # Act
    response = auth_client.post("/posts/", data=payload, format="json")

    # Assert
    assert response.status_code == 201
    assert response.data["author"]["id"] == str(user.id)


def test_posts_delete_by_author(auth_client, user):
    # Arrange
    post = Post.objects.create(author=user, text="to delete")
    url = f"/posts/{post.id}/"

    # Act
    response = auth_client.delete(url)

    # Assert
    assert response.status_code == 204
    refreshed = Post.objects.filter(id=post.id).first()
    if refreshed is None:
        assert True
    else:
        assert getattr(refreshed, "is_deleted", False) is True


def test_posts_delete_by_non_author_forbidden(api_client, user, user_factory):
    # Arrange
    other = user_factory()
    post = Post.objects.create(author=other, text="foreign")
    client = api_client
    client.force_authenticate(user=user)
    url = f"/posts/{post.id}/"

    # Act
    response = client.delete(url)

    # Assert
    assert response.status_code == 403


def test_posts_comments_list(api_client, user):
    # Arrange
    post = Post.objects.create(author=user, text="with comments")
    c1 = Comment.objects.create(post=post, author=user, text="first")
    c2 = Comment.objects.create(post=post, author=user, text="second")
    url = f"/posts/{post.id}/comments/"

    # Act
    response = api_client.get(url)

    # Assert
    assert response.status_code == 200
    ids = [i["id"] for i in response.data["results"]]
    assert ids == [str(c1.id), str(c2.id)]


def test_posts_comments_create_requires_auth(api_client, user):
    # Arrange
    post = Post.objects.create(author=user, text="no auth")
    url = f"/posts/{post.id}/comments/"
    payload = {"text": "anon"}

    # Act
    response = api_client.post(url, data=payload, format="json")

    # Assert
    assert response.status_code in (401, 403)


def test_posts_comments_create_success(auth_client, user):
    # Arrange
    post = Post.objects.create(author=user, text="com create")
    url = f"/posts/{post.id}/comments/"
    payload = {"text": "nice!"}

    # Act
    response = auth_client.post(url, data=payload, format="json")

    # Assert
    assert response.status_code == 201
    assert response.data["author"]["id"] == str(user.id)
    assert Comment.objects.filter(text="nice!", post=post).exists()


def test_posts_react_add_like(auth_client, user):
    # Arrange
    post = Post.objects.create(author=user, text="react")
    url = f"/posts/{post.id}/react/"

    # Act
    response = auth_client.post(url, data={"type": "like"}, format="json")

    # Assert
    assert response.status_code == 200
    assert response.data["status"] == "added"


def test_posts_react_toggle_like_dislike_remove(auth_client, user):
    # Arrange
    post = Post.objects.create(author=user, text="react2")
    url = f"/posts/{post.id}/react/"

    # Act
    r1 = auth_client.post(url, data={"type": "like"}, format="json")
    r2 = auth_client.post(url, data={"type": "dislike"}, format="json")
    r3 = auth_client.post(url, data={"type": "dislike"}, format="json")

    # Assert
    assert r1.data["status"] == "added"
    assert r2.data["status"] == "changed"
    assert r3.data["status"] == "removed"


def test_posts_feed_requires_auth(api_client):
    # Arrange
    # Act
    response = api_client.get("/posts/feed/")

    # Assert
    assert response.status_code in (401, 403)


def test_posts_feed_returns_empty_if_no_follows(auth_client, user, user_factory):
    # Arrange
    other = user_factory()
    Post.objects.create(author=other, text="a")
    Post.objects.create(author=other, text="b")

    # Act
    response = auth_client.get("/posts/feed/")

    # Assert
    assert response.status_code == 200
    assert response.data["results"] == []


def test_posts_liked_by_me_requires_auth(api_client):
    # Arrange
    # Act
    response = api_client.get("/posts/me/liked/")

    # Assert
    assert response.status_code in (401, 403)


def test_posts_liked_by_me_returns_only_liked(auth_client, user, user_factory):
    # Arrange
    author = user_factory()
    p1 = Post.objects.create(author=author, text="like me")
    p2 = Post.objects.create(author=author, text="dont")
    PostReaction.objects.create(post=p1, user=user, type=PostReaction.LIKE)

    # Act
    response = auth_client.get("/posts/me/liked/")

    # Assert
    assert response.status_code == 200
    ids = [i["id"] for i in response.data["results"]]
    assert ids == [str(p1.id)]


def test_posts_search_requires_query_param(api_client, user):
    # Arrange
    Post.objects.create(author=user, text="some text")

    # Act
    response = api_client.get("/posts/search/")

    # Assert
    assert response.status_code == 400
    assert "q" in response.data


def test_posts_search_filters_by_text(api_client, user):
    # Arrange
    p1 = Post.objects.create(author=user, text="Charizard holo card")
    p2 = Post.objects.create(author=user, text="something else")
    p3 = Post.objects.create(author=user, text="charizard mentioned again")

    # Act
    response = api_client.get("/posts/search/?q=charizard")

    # Assert
    assert response.status_code == 200
    texts = [i["text"] for i in response.data["results"]]
    assert p1.text in texts
    assert p3.text in texts
    assert p2.text not in texts
