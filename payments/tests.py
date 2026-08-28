from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import Payment, CommissionRule, Escrow
from deals.models import DealRoom
from listings.models import Listing, Category

User = get_user_model()

class PaymentModelTest(TestCase):
    """Test Payment models"""
    
    def setUp(self):
        self.buyer = User.objects.create_user(
            username='buyer',
            email='buyer@test.com',
            password='BuyerPass123!',
            phone_number='0712345678',
            role='MTEJA'
        )
        
        self.seller = User.objects.create_user(
            username='seller',
            email='seller@test.com',
            password='SellerPass123!',
            phone_number='0712345679',
            role='DALALI'
        )
        
        self.category = Category.objects.create(name='Land')
        self.listing = Listing.objects.create(
            title='Test Property',
            description='Test description',
            property_type='LAND',
            category=self.category,
            location='Dar es Salaam',
            price=1000000,
            size=100,
            seller=self.seller
        )
        
        self.deal = DealRoom.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            seller=self.seller,
            original_price=1000000
        )
    
    def test_create_payment(self):
        """Test creating a payment"""
        payment = Payment.objects.create(
            deal_room=self.deal,
            buyer=self.buyer,
            seller=self.seller,
            amount=1000000,
            commission=50000,
            net_amount=950000,
            payment_method='M_PESA'
        )
        self.assertEqual(payment.status, 'PENDING')
        self.assertEqual(payment.amount, 1000000)
        self.assertEqual(payment.commission, 50000)
        self.assertEqual(payment.net_amount, 950000)
    
    def test_calculate_commission(self):
        """Test commission calculation"""
        payment = Payment.objects.create(
            deal_room=self.deal,
            buyer=self.buyer,
            seller=self.seller,
            amount=1000000,
            commission=0,
            net_amount=0,
            payment_method='M_PESA'
        )
        commission = payment.calculate_commission(5.0)
        self.assertEqual(commission, 50000)
    
    def test_payment_str_method(self):
        """Test the string representation"""
        payment = Payment.objects.create(
            deal_room=self.deal,
            buyer=self.buyer,
            seller=self.seller,
            amount=1000000,
            commission=50000,
            net_amount=950000,
            payment_method='M_PESA'
        )
        self.assertIn('Payment', str(payment))

class PaymentAPITest(APITestCase):
    """Test Payment API endpoints"""
    
    def setUp(self):
        self.buyer = User.objects.create_user(
            username='buyer',
            email='buyer@test.com',
            password='BuyerPass123!',
            phone_number='0712345678',
            role='MTEJA'
        )
        
        self.seller = User.objects.create_user(
            username='seller',
            email='seller@test.com',
            password='SellerPass123!',
            phone_number='0712345679',
            role='DALALI'
        )
        
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='AdminPass123!',
            phone_number='0712345680',
            role='ADMIN'
        )
        
        self.category = Category.objects.create(name='Land')
        self.listing = Listing.objects.create(
            title='Test Property',
            description='Test description',
            property_type='LAND',
            category=self.category,
            location='Dar es Salaam',
            price=1000000,
            size=100,
            seller=self.seller
        )
        
        self.deal = DealRoom.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            seller=self.seller,
            original_price=1000000
        )
        
        # Create commission rule
        CommissionRule.objects.create(
            name='Default Commission',
            rate=5.00,
            is_active=True
        )
    
    def test_create_payment(self):
        """Test creating a payment via API"""
        self.client.force_authenticate(user=self.buyer)
        url = reverse('payments-list')
        data = {
            'deal_room': self.deal.id,
            'buyer': self.buyer.id,
            'seller': self.seller.id,
            'amount': 1000000,
            'payment_method': 'M_PESA'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'PENDING')
        self.assertEqual(float(response.data['commission']), 50000.00)
        self.assertEqual(float(response.data['net_amount']), 950000.00)
    
    def test_get_payment_detail(self):
        """Test getting payment detail"""
        payment = Payment.objects.create(
            deal_room=self.deal,
            buyer=self.buyer,
            seller=self.seller,
            amount=1000000,
            commission=50000,
            net_amount=950000,
            payment_method='M_PESA'
        )
        
        self.client.force_authenticate(user=self.buyer)
        url = reverse('payments-detail', kwargs={'pk': payment.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], payment.id)
    
    def test_update_payment_status(self):
        """Test updating payment status"""
        payment = Payment.objects.create(
            deal_room=self.deal,
            buyer=self.buyer,
            seller=self.seller,
            amount=1000000,
            commission=50000,
            net_amount=950000,
            payment_method='M_PESA'
        )
        
        self.client.force_authenticate(user=self.admin)
        url = reverse('payments-detail', kwargs={'pk': payment.id})
        data = {'status': 'COMPLETED'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'COMPLETED')