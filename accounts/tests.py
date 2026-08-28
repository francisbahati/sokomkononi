from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

User = get_user_model()

class UserModelTest(TestCase):
    """Test User model"""
    
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@email.com',
            'phone_number': '0712345678',
            'password': 'TestPass123!',
            'role': 'MTEJA'
        }
    
    def test_create_user(self):
        """Test creating a user"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@email.com')
        self.assertEqual(user.phone_number, '0712345678')
        self.assertEqual(user.role, 'MTEJA')
        self.assertTrue(user.check_password('TestPass123!'))
    
    def test_user_str_method(self):
        """Test the string representation"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'testuser (Mteja)')
    
    def test_user_roles(self):
        """Test user roles exist"""
        self.assertEqual(User.Role.ADMIN, 'ADMIN')
        self.assertEqual(User.Role.DALALI, 'DALALI')
        self.assertEqual(User.Role.MTEJA, 'MTEJA')

class UserAPITest(APITestCase):
    """Test User API endpoints"""
    
    def test_user_registration(self):
        """Test user registration endpoint"""
        url = reverse('register')
        data = {
            'username': 'newuser',
            'email': 'new@email.com',
            'phone_number': '0712345679',
            'password': 'NewPass123!',
            'confirm_password': 'NewPass123!',
            'role': 'MTEJA'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('user', response.data)