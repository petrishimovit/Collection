from django.db import reset_queries
import pytest
from apps.accounts.models import User, Follow



@pytest.mark.django_db
def test_user_profile_auto_create():

    u = User.objects.create_user(email="a@a.com", display_name="A", password="12345")

    assert u.profile.bio == ""

    assert u.display_name == "A"

    assert u.profile.collection_focus == ""


@pytest.mark.django_db
def test_user_cannot_update_other_user_profile(auth_client):

    u = User.objects.create_user(email="a@a.com", display_name="A", password="12345")

    response = auth_client.put(
        f"/users/{u.id}/profile/",
        {
            "display_name": "New Petr",
            "profile": 
            {
            "bio": "Updated",
            "website": "https://example.com"
            }
        },

        format='json')
    
    assert response.status_code == 403



@pytest.mark.django_db
def test_user_update_profile(auth_client):

    response = auth_client.get("/users/me/").data

    response = auth_client.put(
        f"/users/{response['id']}/profile/",
        {
            "display_name": "New Petr",
            "profile": 
            {
            "bio": "Updated",
            "website": "https://example.com"
            }
        },

        format='json')
        
    
    assert response.status_code == 200

    