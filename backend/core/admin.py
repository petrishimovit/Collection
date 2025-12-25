from django.contrib import admin


class BaseAdmin(admin.ModelAdmin):
    """
    Base Admin class need for all_objects queryset in every model
    """

    def get_queryset(self, request):
        manager = getattr(self.model, "all_objects", self.model._default_manager)
        return manager.get_queryset()
