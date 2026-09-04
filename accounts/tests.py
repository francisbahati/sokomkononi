from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import User

class UserModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@email.com',
            'phone_number': '0712345678',
            'password': 'TestPass123!',
            'role': 'MTEJA'
        }

    def test_create_user(self):
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.status, User.Status.PENDING)

    def test_get_by_contact(self):
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(User.get_by_contact('0712345678'), user)
        self.assertEqual(User.get_by_contact('test@email.com'), user)

class AuthenticationAPITest(APITestCase):
    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.admin_login_url = reverse('admin-login')
        self.registration_data = {
            'name': 'newuser',
            'contact': '0712345679',
            'password': 'NewPass123!',
            'confirm_password': 'NewPass123!',
            'role': 'MTEJA'
        }

    def test_user_registration(self):
        response = self.client.post(self.register_url, self.registration_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        user = User.objects.get(phone_number='0712345679')
        self.assertEqual(user.status, User.Status.PENDING)

    def test_user_login(self):
        # Register first
        self.client.post(self.register_url, self.registration_data, format='json')
        # Login
        login_data = {
            'contact': '0712345679',
            'password': 'NewPass123!',
            'role': 'MTEJA'
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)

    def test_admin_login_fails_for_mteja(self):
        # Register Mteja
        self.client.post(self.register_url, self.registration_data, format='json')
        # Try admin login
        login_data = {
            'contact': '0712345679',
            'password': 'NewPass123!'
        }
        response = self.client.post(self.admin_login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)