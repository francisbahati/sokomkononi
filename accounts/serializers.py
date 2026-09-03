from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, OTP, UserFavorite
import re

User = get_user_model()


def validate_tanzanian_phone_number(value):
    """Validate Tanzanian phone number format."""
    if not value:
        return value
    # Remove any spaces or dashes
    value = re.sub(r'[\s\-]', '', value)
    # Check if it starts with +255 followed by 9 digits (total 13)
    if re.match(r'^\+255\d{9}$', value):
        return value
    # Check if it starts with 0 followed by 9 digits (total 10)
    if re.match(r'^0\d{9}$', value):
        return value
    raise serializers.ValidationError(
        "Phone number must be a valid Tanzanian number: either +255XXXXXXXXX or 0XXXXXXXXX (10 digits)."
    )


class UserRegistrationSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='username', required=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    phone_number = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('name', 'email', 'phone_number', 'password', 'confirm_password', 'role')
        extra_kwargs = {'role': {'required': True}}

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate_email(self, value):
        if not value:
            return None
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_phone_number(self, value):
        if not value:
            return None
        # Validate Tanzanian phone number
        validated = validate_tanzanian_phone_number(value)
        # Check uniqueness
        if User.objects.filter(phone_number=validated).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return validated

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        # Ensure at least one of email or phone_number is provided
        if not attrs.get('email') and not attrs.get('phone_number'):
            raise serializers.ValidationError("At least one of email or phone number is required.")
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        username = validated_data.pop('username')
        email = validated_data.pop('email', None)
        phone_number = validated_data.pop('phone_number', None)
        password = validated_data.pop('password')
        role = validated_data.get('role', User.Role.MTEJA)

        user = User.objects.create_user(
            username=username,
            email=email,
            phone_number=phone_number,
            password=password,
            role=role,
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


# ---------- OTP serializers ----------
class OTPSendSerializer(serializers.Serializer):
    contact = serializers.CharField(required=True)
    purpose = serializers.ChoiceField(choices=OTP.PURPOSE_CHOICES, default='login')

    def validate_contact(self, value):
        if not User.get_by_contact(value):
            raise serializers.ValidationError("No user found with this contact.")
        return value


class OTPVerifySerializer(serializers.Serializer):
    contact = serializers.CharField(required=True)
    code = serializers.CharField(required=True, min_length=6, max_length=6)
    purpose = serializers.ChoiceField(choices=OTP.PURPOSE_CHOICES, default='login')


# ---------- Favorites serializers ----------
class FavoriteSerializer(serializers.ModelSerializer):
    listing_details = serializers.SerializerMethodField()

    class Meta:
        model = UserFavorite
        fields = ['id', 'user', 'listing', 'listing_details', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def get_listing_details(self, obj):
        from listings.serializers import ListingListSerializer
        return ListingListSerializer(obj.listing, context=self.context).data


class FavoriteToggleSerializer(serializers.Serializer):
    listing_id = serializers.IntegerField(required=True)