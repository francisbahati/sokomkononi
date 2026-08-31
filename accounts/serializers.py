from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='username', required=True)
    contact = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('name', 'contact', 'password', 'confirm_password', 'role')
        extra_kwargs = {'role': {'required': True}}

    def validate_contact(self, value):
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        contact = validated_data.pop('contact')
        username = validated_data.pop('username')
        email = contact if '@' in contact else None
        phone_number = contact
        user = User.objects.create_user(
            username=username,
            phone_number=phone_number,
            email=email,
            password=validated_data['password'],
            role=validated_data.get('role', User.Role.MTEJA),
            status=User.Status.PENDING,
            is_active=True
        )
        return user


class LoginSerializer(serializers.Serializer):
    contact = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    role = serializers.ChoiceField(choices=User.Role.choices, required=False)

    def validate(self, attrs):
        contact = attrs.get('contact')
        password = attrs.get('password')
        role = attrs.get('role')

        user = User.get_by_contact(contact)
        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        if not user.check_password(password):
            raise serializers.ValidationError("Invalid credentials.")
        if role and user.role != role:
            raise serializers.ValidationError(f"Invalid role. Expected {role}.")
        if user.status == User.Status.BLOCKED:
            raise serializers.ValidationError("This account has been blocked.")
        if user.status == User.Status.SUSPENDED:
            raise serializers.ValidationError("This account is suspended.")

        attrs['user'] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'role',
                  'status', 'is_verified', 'profile_photo', 'bio', 'created_at']
        read_only_fields = ['id', 'status', 'is_verified', 'created_at', 'role']


class UserKYCSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id_card_number', 'id_card_photo']


class PasswordResetRequestSerializer(serializers.Serializer):
    contact = serializers.EmailField(required=True)

    def validate_contact(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user with that email address.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    uid = serializers.CharField(required=True)


class AdminUserListSerializer(serializers.ModelSerializer):
    listings_count = serializers.IntegerField(source='listings.count', read_only=True)
    purchases_count = serializers.IntegerField(source='deals_as_buyer.count', read_only=True)
    joined_at = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone_number', 'role',
            'status', 'is_verified', 'joined_at', 'listings_count', 'purchases_count'
        ]
        read_only_fields = ['id', 'joined_at']


class AdminUserStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['status', 'is_verified']

    def update(self, instance, validated_data):
        if 'is_verified' in validated_data and validated_data['is_verified']:
            instance.is_verified = True
            instance.status = User.Status.ACTIVE
        if 'status' in validated_data:
            instance.status = validated_data['status']
        instance.save()
        return instance


class VerificationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'role',
                  'is_verified', 'id_card_number', 'id_card_photo', 'created_at']
        read_only_fields = ['id', 'username', 'email', 'phone_number', 'role',
                            'created_at']