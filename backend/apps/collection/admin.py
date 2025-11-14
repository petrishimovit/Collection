from django.contrib import admin
from django.utils.html import format_html
from .models import Collection, Item, ItemImage

admin.register(Collection)
admin.register(Item)
admin.register(ItemImage)