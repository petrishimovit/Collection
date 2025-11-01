from rest_framework import serializers

class GameItemSerializer(serializers.Serializer):
    Game = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    GameLink = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    Year = serializers.IntegerField(required=False, allow_null=True)
    Dev = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    DevLink = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    Publisher = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    PublisherLink = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    Platform = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    PlatformLink = serializers.CharField(required=False, allow_blank=True, allow_null=True)



class SearchQuerySerializer(serializers.Serializer):
    q = serializers.CharField(max_length=200)
    region = serializers.ChoiceField(
        choices=["all", "japan", "ntsc", "pal"],
        required=False,
        default="all",
    )
    limit = serializers.IntegerField(required=False, min_value=1, max_value=50, default=10)


class ItemQuerySerializer(serializers.Serializer):
    url = serializers.URLField(required=False)
    slug = serializers.CharField(required=False)

    def validate(self, data):
        if not data.get("url") and not data.get("slug"):
            raise serializers.ValidationError("Provide `url` or `slug`.")
        return data