from django.contrib import admin
from .models import Post, Comment,PostReaction,PostImage

admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(PostReaction)
admin.site.register(PostImage)