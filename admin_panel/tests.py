from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import PlatformSettings, CommissionRule, Dispute
from deals.models import DealRoom, Listing
from listings.models import Category

User = get_user_model()


class AdminPanelTest(APITestCase):
    """Test admin panel functionality"""

    def setUp(self):
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='AdminPass123!',
            phone_number='0712345678',
            role='ADMIN'
        )

        # Create regular user
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@test.com',
            password='UserPass123!',
            phone_number='0712345679',
            role='MTEJA'
        )

        # Create a listing for testing
        self.category = Category.objects.create(name='Land')
        self.listing = Listing.objects.create(
            title='Test Property',
            description='Test description',
            property_type='LAND',
            category=self.category,
            location='Dar es Salaam',
            price=1000000,
            size=100,
            seller=self.regular_user
        )

        # Create a deal room
        self.deal = DealRoom.objects.create(
            listing=self.listing,
            buyer=self.regular_user,
            seller=self.regular_user,
            original_price=1000000,
            status='NEGOTIATING'
        )

    def test_admin_permission(self):
        """Test that only admins can access admin endpoints"""
        url = reverse('admin-dashboard-stats')

        # Test without authentication
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test with regular user
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test with admin user
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_commission_rule(self):
        """Test creating commission rule"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('commission-rules')
        data = {
            'name': 'Standard Commission',
            'rate': 5.00,
            'description': 'Standard platform commission',
            'is_active': True
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['rate'], '5.00')

    def test_create_dispute(self):
        """Test creating a dispute"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('disputes')
        data = {
            'deal_room': self.deal.id,
            'description': 'Test dispute description'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'OPEN')

    def test_resolve_dispute(self):
        """Test resolving a dispute"""
        self.client.force_authenticate(user=self.admin_user)

        # Create a dispute
        dispute = Dispute.objects.create(
            deal_room=self.deal,
            raised_by=self.regular_user,
            description='Test dispute'
        )

        # Resolve it
        url = reverse('dispute-resolve', kwargs={'pk': dispute.id})
        data = {
            'status': 'RESOLVED',
            'resolution_notes': 'Resolved in favor of buyer'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check it was resolved
        dispute.refresh_from_db()
        self.assertEqual(dispute.status, 'RESOLVED')
        self.assertEqual(dispute.resolved_by, self.admin_user)


class PlatformSettingsTest(APITestCase):
    """Test platform settings"""

    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='AdminPass123!',
            phone_number='0712345678',
            role='ADMIN'
        )

        # Create a setting
        self.setting = PlatformSettings.objects.create(
            setting_key='commission_rate',
            setting_value='5.00',
            setting_type='DECIMAL',
            description='Default commission rate'
        )

    def test_update_setting(self):
        """Test updating platform setting"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('platform-settings-detail', kwargs={'pk': self.setting.id})
        data = {
            'setting_value': '7.50'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['setting_value'], '7.50')

    def test_get_setting_by_key(self):
        """Test getting setting by key"""
        self.client.force_authenticate(user=self.admin_user)
        url = f"{reverse('platform-settings')}?key=commission_rate"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['setting_value'], '5.00')