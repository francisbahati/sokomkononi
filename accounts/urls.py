from django.urls import path
from .views import (
    RegisterView, LoginView, AdminLoginView, LogoutView, MeView,
    ProfileView, SubmitKYCView, ForgotPasswordView, ResetPasswordView,
    VerificationStatusView,
    AdminUserListView, AdminUserVerifyView, AdminUserSuspendView,
    AdminUserReactivateView, AdminUserBlockView, AdminVerificationRequestsView,
    RequestOTPView, VerifyOTPView, SocialLoginCallbackView,
    FavoriteView
)

urlpatterns = [
    # Auth
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('admin-login/', AdminLoginView.as_view(), name='admin-login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('kyc/', SubmitKYCView.as_view(), name='submit-kyc'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('verification-status/', VerificationStatusView.as_view(), name='verification-status'),

    # Admin user management
    path('admin/users/', AdminUserListView.as_view(), name='admin-users'),
    path('admin/users/<int:pk>/verify/', AdminUserVerifyView.as_view(), name='admin-user-verify'),
    path('admin/users/<int:pk>/suspend/', AdminUserSuspendView.as_view(), name='admin-user-suspend'),
    path('admin/users/<int:pk>/reactivate/', AdminUserReactivateView.as_view(), name='admin-user-reactivate'),
    path('admin/users/<int:pk>/block/', AdminUserBlockView.as_view(), name='admin-user-block'),
    path('admin/verification-requests/', AdminVerificationRequestsView.as_view(), name='admin-verification-requests'),

    # OTP
    path('otp/request/', RequestOTPView.as_view(), name='otp-request'),
    path('otp/verify/', VerifyOTPView.as_view(), name='otp-verify'),

    # Social login callback (to return JSON after Google OAuth)
    path('social/callback/', SocialLoginCallbackView.as_view(), name='social-callback'),

    # Favorites
    path('favorites/', FavoriteView.as_view(), name='favorites'),
]