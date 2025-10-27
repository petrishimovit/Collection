from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework import serializers
from accounts.models import User
from .profile import ProfileBaseSerializer, ProfileDetailSerializer

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "display_name")

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


class UserListSerializer(serializers.ModelSerializer):
    
    profile = ProfileBaseSerializer(read_only=True)

    class Meta:
        model = User
        fields = ("id", "display_name", "profile")
        read_only_fields = fields


class UserDetailSerializer(UserListSerializer):
    
    email = serializers.EmailField(read_only=True)
    profile = ProfileDetailSerializer(read_only=True)

    followers_count = serializers.IntegerField(read_only=True, source="followers_count")
    following_count = serializers.IntegerField(read_only=True, source="following_count")
    is_following = serializers.SerializerMethodField()
    is_self = serializers.SerializerMethodField()

    class Meta(UserListSerializer.Meta):
        fields = UserListSerializer.Meta.fields + (
            "email",
            "followers_count",
            "following_count",
            "is_following",
            "is_self",
        )
        read_only_fields = fields

    def get_is_following(self, obj: User) -> bool:
        
        request = self.context.get("request")
        if not request or not request.user or not request.user.is_authenticated:
            return False
        if request.user.id == obj.id:
            return False
        return request.user.is_following(obj)

    def get_is_self(self, obj: User) -> bool:
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and request.user.id == obj.id)


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
