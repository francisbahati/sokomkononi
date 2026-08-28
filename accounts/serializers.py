from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'phone_number', 'role', 'password', 'confirm_password')
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
            'phone_number': {'required': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password didn't match."})
        return attrs

    def create(self, validated_data):
        # Remove confirm_password before creating user
        validated_data.pop('confirm_password')
        
        # Create user with hashed password using create_user
        user = User.objects.create_user(**validated_data)
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'role', 
                 'is_verified', 'profile_photo', 'bio', 'created_at']
        read_only_fields = ['id', 'is_verified', 'created_at']

class UserKYCSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id_card_number', 'id_card_photo']