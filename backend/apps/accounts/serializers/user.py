from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework import serializers
from apps.accounts.models import User
from .profile import ProfileBaseSerializer, ProfileDetailSerializer

User = get_user_model()

class UserListSerializer(serializers.ModelSerializer):
    profile = ProfileBaseSerializer(read_only=True)
    class Meta:
        model = User
        fields = ("id", "display_name", "profile")
        read_only_fields = fields

class UserDetailSerializer(UserListSerializer):
    
    profile = ProfileDetailSerializer(read_only=True)
    followers_count = serializers.IntegerField(read_only=True)
    following_count = serializers.IntegerField(read_only=True)
    is_following = serializers.SerializerMethodField()
    is_self = serializers.SerializerMethodField()

    class Meta(UserListSerializer.Meta):
        fields = UserListSerializer.Meta.fields + (
            "followers_count", "following_count", "is_following", "is_self",
        )
        read_only_fields = fields

    def get_is_following(self, obj):
        req = self.context.get("request")
        if not req or not req.user.is_authenticated or req.user.id == obj.id:
            return False
        return req.user.is_following(obj)

    def get_is_self(self, obj):
        req = self.context.get("request")
        return bool(req and req.user.is_authenticated and req.user.id == obj.id)

class MeMinimalSerializer(serializers.ModelSerializer):
    profile = ProfileBaseSerializer(read_only=True)
    class Meta:
        model = User
        fields = ("id", "display_name", "profile")
        read_only_fields = fields

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all(), message="email already use")]
    )
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("email", "display_name", "password")

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
