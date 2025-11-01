from django.contrib import admin
from .models import PriceChartingConnect

@admin.register(PriceChartingConnect)
class PriceChartingConnectAdmin(admin.ModelAdmin):
    list_display = ("id", "url", "items_count", "last_synced_at", "created_at")
    search_fields = ("url",)
    readonly_fields = ("created_at", "updated_at", "last_synced_at")
    ordering = ("-created_at",)

    def items_count(self, obj):
        return obj.items.count()
