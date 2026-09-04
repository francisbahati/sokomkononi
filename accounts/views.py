from rest_framework import generics, status, permissions, viewsets, mixins, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import (
    UserRegistrationSerializer, LoginSerializer, UserProfileSerializer,
    UserKYCSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    AdminUserListSerializer, AdminUserStatusUpdateSerializer, VerificationRequestSerializer,
    OTPSendSerializer, OTPVerifySerializer,
    FavoriteSerializer, FavoriteToggleSerializer
)
from .permissions import IsDalali, IsAdmin, IsMteja
from admin_panel.permissions import IsPlatformAdmin
from .models import User, OTP, UserFavorite
from .utils import send_otp
from listings.models import Listing

User = get_user_model()

# ---------- Dummy serializer for schema ----------
class EmptySerializer(serializers.Serializer):
    pass


# ---------- Registration & Login ----------
class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return Response({
                'user': UserProfileSerializer(user).data,
                'message': 'Registration successful.'
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                'error': str(e),
                'traceback': traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = EmptySerializer

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return Response({
            'user': UserProfileSerializer(user).data,
            'message': 'Login successful.'
        })


class AdminLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = EmptySerializer

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        if user.role != User.Role.ADMIN:
            return Response(
                {'error': 'Access denied. Admin privileges required.'},
                status=status.HTTP_403_FORBIDDEN
            )
        login(request, user)
        return Response({
            'user': UserProfileSerializer(user).data,
            'message': 'Admin login successful.'
        })


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EmptySerializer

    def post(self, request):
        logout(request)
        return Response({'message': 'Logout successful.'})


class MeView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class SubmitKYCView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsDalali]
    serializer_class = EmptySerializer

    def post(self, request):
        serializer = UserKYCSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': 'KYC documents submitted for verification.',
            'status': 'pending'
        })


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = EmptySerializer

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['contact']
        user = User.objects.get(email=email)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
        send_mail(
            subject='SokoMkononi Password Reset',
            message=f'Click the link to reset your password: {reset_link}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return Response({'message': 'Password reset link sent to your email.'})


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = EmptySerializer

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        uid = request.data.get('uid')
        if not uid:
            return Response({'error': 'UID required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({'error': 'Invalid user.'}, status=status.HTTP_400_BAD_REQUEST)
        if not default_token_generator.check_token(user, token):
            return Response({'error': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        return Response({'message': 'Password reset successful.'})


class VerificationStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EmptySerializer

    def get(self, request):
        user = request.user
        if user.role != User.Role.DALALI:
            return Response({'status': 'none'})
        if user.is_verified:
            return Response({'status': 'verified'})
        if user.id_card_number or user.id_card_photo:
            return Response({'status': 'pending'})
        return Response({'status': 'none'})


# ---------- Admin user management ----------
class AdminUserListView(generics.ListAPIView):
    serializer_class = AdminUserListSerializer
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['role', 'status']

    def get_queryset(self):
        return User.objects.all().order_by('-created_at')


class AdminUserVerifyView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    queryset = User.objects.all()
    serializer_class = EmptySerializer

    def patch(self, request, pk):
        user = self.get_object()
        user.is_verified = True
        user.status = User.Status.ACTIVE
        user.save()
        return Response({'status': 'verified', 'user': AdminUserListSerializer(user).data})


class AdminUserSuspendView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    queryset = User.objects.all()
    serializer_class = EmptySerializer

    def patch(self, request, pk):
        user = self.get_object()
        user.status = User.Status.SUSPENDED
        user.save()
        return Response({'status': 'suspended', 'user': AdminUserListSerializer(user).data})


class AdminUserReactivateView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    queryset = User.objects.all()
    serializer_class = EmptySerializer

    def patch(self, request, pk):
        user = self.get_object()
        user.status = User.Status.ACTIVE
        user.save()
        return Response({'status': 'reactivated', 'user': AdminUserListSerializer(user).data})


class AdminUserBlockView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    queryset = User.objects.all()
    serializer_class = EmptySerializer

    def patch(self, request, pk):
        user = self.get_object()
        user.status = User.Status.BLOCKED
        user.save()
        return Response({'status': 'blocked', 'user': AdminUserListSerializer(user).data})


class AdminVerificationRequestsView(generics.ListAPIView):
    serializer_class = VerificationRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]

    def get_queryset(self):
        return User.objects.filter(role=User.Role.DALALI, is_verified=False).order_by('-created_at')


# ---------- OTP Views ----------
class RequestOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = EmptySerializer

    def post(self, request):
        serializer = OTPSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact = serializer.validated_data['contact']
        purpose = serializer.validated_data['purpose']
        user = User.get_by_contact(contact)
        if not user:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        otp = send_otp(user, purpose, contact)
        if otp:
            return Response({'message': f'OTP sent to {contact}'})
        else:
            return Response({'error': 'Failed to send OTP'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = EmptySerializer

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact = serializer.validated_data['contact']
        code = serializer.validated_data['code']
        purpose = serializer.validated_data['purpose']
        user = User.get_by_contact(contact)
        if not user:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        otp = OTP.objects.filter(user=user, code=code, purpose=purpose, is_used=False).first()
        if not otp or not otp.is_valid():
            return Response({'error': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)

        otp.is_used = True
        otp.save()

        if purpose == 'verify':
            user.email_verified = True
            user.save()
            return Response({'message': 'Email verified successfully'})

        if purpose == 'login':
            login(request, user)
            return Response({
                'user': UserProfileSerializer(user).data,
                'message': 'Login successful'
            })
        elif purpose == 'reset':
            return Response({'message': 'OTP verified. You can now reset your password.'})

        return Response({'message': 'OTP verified'})


# ---------- Social Login Callback ----------
class SocialLoginCallbackView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = EmptySerializer

    def get(self, request):
        if request.user.is_authenticated:
            return Response({
                'user': UserProfileSerializer(request.user).data,
                'message': 'Social login successful'
            })
        else:
            return Response({'error': 'Authentication failed'}, status=status.HTTP_401_UNAUTHORIZED)


# ---------- Favorites ----------
class FavoriteView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsMteja]
    serializer_class = EmptySerializer

    def get(self, request):
        favorites = UserFavorite.objects.filter(user=request.user)
        serializer = FavoriteSerializer(favorites, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        serializer = FavoriteToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        listing_id = serializer.validated_data['listing_id']
        try:
            listing = Listing.objects.get(id=listing_id)
        except Listing.DoesNotExist:
            return Response({'error': 'Listing not found'}, status=status.HTTP_404_NOT_FOUND)

        favorite, created = UserFavorite.objects.get_or_create(user=request.user, listing=listing)
        if not created:
            favorite.delete()
            return Response({'message': 'Favorite removed'})
        return Response({'message': 'Favorite added'}, status=status.HTTP_201_CREATED)