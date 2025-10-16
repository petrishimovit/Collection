from django.contrib import admin
from django.utils.html import format_html
from .models import Collection, Item, ItemImage


class ItemImageInline(admin.TabularInline):
    model = ItemImage
    extra = 0
    fields = ("preview", "image", "order", "created_at", "updated_at","description")
    readonly_fields = ("preview", "created_at", "updated_at")

    @admin.display(description="Preview")
    def preview(self, obj):
        if not obj.image:
            return "—"
        return format_html('<img src="{}" style="height:60px;border-radius:6px" />', obj.image.url)


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "items_count", "created_at")
    search_fields = ("name", "owner__email", "owner__display_name")
    list_filter = ("owner",)
    autocomplete_fields = ("owner",)
    readonly_fields = ("created_at", "updated_at")
    fields = ("owner", "name", "image", "created_at", "updated_at")

    @admin.display(description="Items")
    def items_count(self, obj):
        return obj.items.count()


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        "name", "collection", "purchase_date", "purchase_price",
        "current_value", "created_at","description"
    )
    search_fields = (
        "name", "collection__name",
        "collection__owner__email", "collection__owner__display_name",
    )
    list_filter = ("collection", "purchase_date")
    autocomplete_fields = ("collection",)
    readonly_fields = ("created_at", "updated_at")
    fields = (
        "collection", "name",
        "purchase_date", "purchase_price", "current_value",
        "extra", "created_at", "updated_at",
    )
    inlines = [ItemImageInline]


@admin.register(ItemImage)
class ItemImageAdmin(admin.ModelAdmin):
    list_display = ("item", "order", "preview", "created_at")
    list_select_related = ("item", "item__collection")
    search_fields = ("item__name", "item__collection__name")
    list_filter = ("order",)
    readonly_fields = ("preview", "created_at", "updated_at")
    fields = ("item", "image", "order", "preview", "created_at", "updated_at")

    @admin.display(description="Preview")
    def preview(self, obj):
        if not obj.image:
            return "—"
        return format_html('<img src="{}" style="height:60px;border-radius:6px" />', obj.image.url)
