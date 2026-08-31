from rest_framework import generics, status, permissions, viewsets
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
    AdminUserListSerializer, AdminUserStatusUpdateSerializer, VerificationRequestSerializer
)
from .permissions import IsDalali, IsAdmin
from admin_panel.permissions import IsPlatformAdmin
from .models import User

User = get_user_model()


# ---------- Registration ----------
class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return Response({
            'user': UserProfileSerializer(user).data,
            'message': 'Registration successful.'
        }, status=status.HTTP_201_CREATED)


# ---------- Login ----------
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return Response({
            'user': UserProfileSerializer(user).data,
            'message': 'Login successful.'
        })


# ---------- Admin Login ----------
class AdminLoginView(APIView):
    permission_classes = [permissions.AllowAny]

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


# ---------- Logout ----------
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'message': 'Logout successful.'})


# ---------- Current User ----------
class MeView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


# ---------- Profile Update ----------
class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


# ---------- KYC Submission ----------
class SubmitKYCView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsDalali]

    def post(self, request):
        serializer = UserKYCSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': 'KYC documents submitted for verification.',
            'status': 'pending'
        })


# ---------- Password Reset ----------
class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

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


# ---------- Seller Verification Status ----------
class VerificationStatusView(APIView):
    """
    GET /api/auth/verification-status/
    Returns the current verification status of the authenticated user.
    Response: { "status": "none" | "pending" | "verified" }
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # Only Dalali have verification status; others get 'none'
        if user.role != User.Role.DALALI:
            return Response({'status': 'none'})

        if user.is_verified:
            return Response({'status': 'verified'})

        # If KYC documents have been submitted but not yet verified
        if user.id_card_number or user.id_card_photo:
            return Response({'status': 'pending'})

        return Response({'status': 'none'})


# ---------- ADMIN USER MANAGEMENT ----------
class AdminUserListView(generics.ListAPIView):
    """Admin: list all users with filters by role and status."""
    serializer_class = AdminUserListSerializer
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['role', 'status']

    def get_queryset(self):
        return User.objects.all().order_by('-created_at')


class AdminUserVerifyView(generics.GenericAPIView):
    """Admin: verify a user (set verified=True, status=ACTIVE)."""
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    queryset = User.objects.all()

    def patch(self, request, pk):
        user = self.get_object()
        user.is_verified = True
        user.status = User.Status.ACTIVE
        user.save()
        return Response({'status': 'verified', 'user': AdminUserListSerializer(user).data})


class AdminUserSuspendView(generics.GenericAPIView):
    """Admin: suspend a user."""
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    queryset = User.objects.all()

    def patch(self, request, pk):
        user = self.get_object()
        user.status = User.Status.SUSPENDED
        user.save()
        return Response({'status': 'suspended', 'user': AdminUserListSerializer(user).data})


class AdminUserReactivateView(generics.GenericAPIView):
    """Admin: reactivate a user (set status=ACTIVE)."""
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    queryset = User.objects.all()

    def patch(self, request, pk):
        user = self.get_object()
        user.status = User.Status.ACTIVE
        user.save()
        return Response({'status': 'reactivated', 'user': AdminUserListSerializer(user).data})


class AdminUserBlockView(generics.GenericAPIView):
    """Admin: block a user."""
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    queryset = User.objects.all()

    def patch(self, request, pk):
        user = self.get_object()
        user.status = User.Status.BLOCKED
        user.save()
        return Response({'status': 'blocked', 'user': AdminUserListSerializer(user).data})


class AdminVerificationRequestsView(generics.ListAPIView):
    """Admin: list pending KYC verification requests (Dalali with is_verified=False)."""
    serializer_class = VerificationRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]

    def get_queryset(self):
        return User.objects.filter(role=User.Role.DALALI, is_verified=False).order_by('-created_at')