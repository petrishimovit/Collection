from django.contrib import admin
from core.admin import BaseAdmin
from .models import Post, Comment, PostReaction, PostImage


@admin.register(Post)
class PostAdmin(BaseAdmin):
    pass


@admin.register(Comment)
class CommentAdmin(BaseAdmin):
    pass


@admin.register(PostReaction)
class PostReactionAdmin(BaseAdmin):
    pass


@admin.register(PostImage)
class PostImageAdmin(BaseAdmin):
    pass
