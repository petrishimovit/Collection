from django.db.models import Prefetch
from django.contrib.auth import get_user_model

User = get_user_model()

def user_list_qs():
   
    return User.objects.filter(is_active=True).select_related("profile").prefetch_related(
      
    )

def user_by_pk(pk: int):
    return user_list_qs().get(pk=pk)

def following_qs(user: User):
   
    return user.following.select_related("profile")

def followers_qs(user):
    
    return User.objects.filter(is_active=True, following__id=user.id)