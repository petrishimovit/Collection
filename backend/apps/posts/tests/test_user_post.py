import pytest

from apps.posts.models import Post

pytestmark = pytest.mark.django_db


def test_user_posts_list_returns_only_user_posts(api_client, user, user_factory):

    # Arrange
    other_user = user_factory()
    p1 = Post.objects.create(author=user, text="user post 1")
    p2 = Post.objects.create(author=user, text="user post 2")
    Post.objects.create(author=other_user, text="other post") 
    url = f"/users/{user.id}/posts/"

    # Act
    response = api_client.get(url)

    # Assert
    assert response.status_code == 200
    assert "results" in response.data
    ids = [item["id"] for item in response.data["results"]]
    assert ids == [str(p2.id), str(p1.id)]  #

def test_user_posts_list_is_paginated_and_ordered(api_client, user):
    
    # Arrange
    posts = [
        Post.objects.create(author=user, text=f"post {i}")
        for i in range(5)
    ]
    url = f"/users/{user.id}/posts/?page_size=2"

    # Act
    response_page_1 = api_client.get(url)
    response_page_2 = api_client.get(url + "&page=2")

    # Assert
    assert response_page_1.status_code == 200
    assert response_page_2.status_code == 200

    
    ids_page_1 = [item["id"] for item in response_page_1.data["results"]]
    assert ids_page_1 == [str(posts[-1].id), str(posts[-2].id)]


    ids_page_2 = [item["id"] for item in response_page_2.data["results"]]
    assert ids_page_2 == [str(posts[-3].id), str(posts[-4].id)]
