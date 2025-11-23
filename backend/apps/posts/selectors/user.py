from apps.accounts.models import User

def following_qs(user: User):
    """
    Return queryset of user`s followers
    """
    return user.following.all()



