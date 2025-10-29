def following_qs(user):
    return user.following.all()
