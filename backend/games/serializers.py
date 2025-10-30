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
