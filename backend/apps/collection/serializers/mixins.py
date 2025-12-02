class HiddenFieldsMixin:


    owner_path = None  
    def _get_owner(self, obj):
        
        if not self.owner_path:
            return None

        target = obj
        for attr in self.owner_path.split("."):
            target = getattr(target, attr, None)
            if target is None:
                break
        return target

    def to_representation(self, instance):
        data = super().to_representation(instance)

        request = self.context.get("request")
        user = getattr(request, "user", None)
        owner = self._get_owner(instance)

        if user and user.is_authenticated and (user == owner or user.is_staff):
            return data

        hidden = getattr(instance, "hidden_fields", None) or []

        for field in hidden:
          
            if field == "extra":
                if "extra" in data:
                    data["extra"] = None
                continue

            if field.startswith("extra."):
                key = field.split(".", 1)[1]
                extra = data.get("extra")
                if isinstance(extra, dict):
                    extra.pop(key, None)
                continue

 
            if field in data:
                data[field] = None

        data.pop("hidden_fields", None)

        return data