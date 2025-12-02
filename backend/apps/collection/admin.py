from django.contrib import admin
from core.admin import BaseAdmin
from .models import Collection, Item, ItemImage


@admin.register(Collection)
class CollectionAdmin(BaseAdmin):
    pass


@admin.register(Item)
class ItemAdmin(BaseAdmin):
    pass


@admin.register(ItemImage)
class ItemImageAdmin(BaseAdmin):
    pass
