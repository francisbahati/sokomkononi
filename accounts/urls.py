from django.urls import path
from .views import RegisterView, ProfileView, SubmitKYCView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('kyc/', SubmitKYCView.as_view(), name='submit-kyc'),
]