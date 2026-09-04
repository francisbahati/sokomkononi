from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import DealRoom, NegotiationMessage
from listings.models import Listing, Category

User = get_user_model()

class DealModelTest(TestCase):
    """Test Deal models"""
    
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
    
    def test_create_deal_room(self):
        """Test creating a deal room"""
        deal = DealRoom.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            seller=self.seller,
            original_price=1000000
        )
        self.assertEqual(deal.status, 'NEGOTIATING')
        self.assertEqual(deal.listing, self.listing)
        self.assertEqual(deal.buyer, self.buyer)
        self.assertEqual(deal.seller, self.seller)
    
    def test_deal_str_method(self):
        """Test the string representation"""
        deal = DealRoom.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            seller=self.seller,
            original_price=1000000
        )
        expected = f"Deal: {self.listing.listing_id} - {self.buyer.username}"
        self.assertEqual(str(deal), expected)
    
    def test_calculate_commission(self):
        """Test commission calculation"""
        deal = DealRoom.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            seller=self.seller,
            original_price=1000000,
            final_price=950000
        )
        commission = deal.calculate_commission(5.0)
        self.assertEqual(commission, 47500)  # 950000 * 0.05
    
    def test_mark_completed(self):
        """Test marking deal as completed"""
        deal = DealRoom.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            seller=self.seller,
            original_price=1000000
        )
        deal.mark_as_completed()
        self.assertEqual(deal.status, 'COMPLETED')
        self.assertIsNotNone(deal.completed_at)

class DealAPITest(APITestCase):
    """Test Deal API endpoints"""
    
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
    
    def test_create_deal(self):
        """Test creating a deal via API"""
        self.client.force_authenticate(user=self.buyer)
        url = reverse('deals-list')
        data = {
            'listing': self.listing.id,
            'buyer': self.buyer.id,
            'seller': self.seller.id,
            'original_price': 1000000
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'NEGOTIATING')
    
    def test_get_deal_detail(self):
        """Test getting deal detail"""
        self.client.force_authenticate(user=self.buyer)
        url = reverse('deals-detail', kwargs={'pk': self.deal.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.deal.id)
    
    def test_send_message(self):
        """Test sending message in deal room"""
        self.client.force_authenticate(user=self.buyer)
        url = reverse('deal-messages', kwargs={'pk': self.deal.id})
        data = {
            'message': 'Hello, I am interested in this property.',
            'is_offer': False
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], data['message'])
    
    def test_send_offer(self):
        """Test sending an offer in deal room"""
        self.client.force_authenticate(user=self.buyer)
        url = reverse('deal-messages', kwargs={'pk': self.deal.id})
        data = {
            'message': 'I offer 900,000',
            'is_offer': True,
            'offer_amount': 900000
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['is_offer'])
        self.assertEqual(response.data['offer_amount'], '900000.00')
    
    def test_get_messages(self):
        """Test getting messages in deal room"""
        # Create some messages
        NegotiationMessage.objects.create(
            deal_room=self.deal,
            sender=self.buyer,
            message='Hello!',
            is_offer=False
        )
        NegotiationMessage.objects.create(
            deal_room=self.deal,
            sender=self.seller,
            message='Hi there!',
            is_offer=False
        )
        
        self.client.force_authenticate(user=self.buyer)
        url = reverse('deal-messages', kwargs={'pk': self.deal.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)