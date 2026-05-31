from rest_framework import serializers
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(write_only=True)
    access = serializers.SerializerMethodField()
    refresh = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ('email', 'password', 'password_confirm', 'access', 'refresh')
        extra_kwargs = {'password': {'write_only': True}}
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password']
        )
        user.generate_new_key()
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'is_active', 'activation_key', 'updated_at')
        read_only_fields = ('id', 'email', 'is_active', 'activation_key', 'updated_at')


class ProxyDetailsSerializer(serializers.Serializer):
    host = serializers.CharField()
    port = serializers.IntegerField()
    protocol = serializers.CharField()
    name = serializers.CharField()

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)