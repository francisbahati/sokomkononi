from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import Notification, UserNotification, NotificationPreference

User = get_user_model()

class NotificationModelTest(TestCase):
    """Test Notification models"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='TestPass123!',
            phone_number='0712345678',
            role='MTEJA'
        )
    
    def test_create_notification(self):
        """Test creating a notification"""
        notification = Notification.objects.create(
            title='Test Notification',
            message='This is a test message',
            notification_type='GENERAL'
        )
        self.assertEqual(notification.title, 'Test Notification')
        self.assertTrue(notification.is_active)
    
    def test_user_notification(self):
        """Test user notification"""
        notification = Notification.objects.create(
            title='Test Notification',
            message='Test message'
        )
        user_notification = UserNotification.objects.create(
            user=self.user,
            notification=notification
        )
        self.assertFalse(user_notification.is_read)
        self.assertIsNone(user_notification.read_at)
        
        # Mark as read
        user_notification.mark_as_read()
        self.assertTrue(user_notification.is_read)
        self.assertIsNotNone(user_notification.read_at)
    
    def test_notification_preference(self):
        """Test notification preferences"""
        pref = NotificationPreference.objects.create(user=self.user)
        self.assertTrue(pref.email_enabled)
        self.assertTrue(pref.in_app_enabled)
        self.assertTrue(pref.deal_updates)

class NotificationAPITest(APITestCase):
    """Test Notification API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='TestPass123!',
            phone_number='0712345678',
            role='MTEJA'
        )
        
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='AdminPass123!',
            phone_number='0712345679',
            role='ADMIN'
        )
        
        self.notification = Notification.objects.create(
            title='Test Notification',
            message='Test message',
            notification_type='GENERAL'
        )
        
        self.user_notification = UserNotification.objects.create(
            user=self.user,
            notification=self.notification
        )
    
    def test_get_user_notifications(self):
        """Test getting user's notifications"""
        self.client.force_authenticate(user=self.user)
        url = reverse('user-notifications')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_mark_notification_read(self):
        """Test marking notification as read"""
        self.client.force_authenticate(user=self.user)
        url = reverse('user-notification-detail', kwargs={'pk': self.user_notification.id})
        data = {'is_read': True}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_read'])
    
    def test_create_notification_as_admin(self):
        """Test creating notification as admin"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('notifications-list')
        data = {
            'title': 'New Notification',
            'message': 'New message',
            'notification_type': 'GENERAL',
            'target_roles': ['MTEJA']
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_get_preferences(self):
        """Test getting user preferences"""
        self.client.force_authenticate(user=self.user)
        url = reverse('preferences')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)