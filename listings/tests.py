from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import Category, Listing, ListingImage
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class ListingModelTest(TestCase):
    """Test Listing models"""
    
    def setUp(self):
        self.seller = User.objects.create_user(
            username='seller',
            email='seller@test.com',
            password='SellerPass123!',
            phone_number='0712345678',
            role='DALALI',
            is_verified=True
        )
        
        self.category = Category.objects.create(
            name='Land',
            description='Land properties'
        )
    
    def test_create_category(self):
        """Test creating a category"""
        category = Category.objects.create(
            name='House',
            description='House properties'
        )
        self.assertEqual(category.name, 'House')
        self.assertIsNotNone(category.slug)
    
    def test_create_listing(self):
        """Test creating a listing"""
        listing = Listing.objects.create(
            title='Test Property',
            description='Beautiful land for sale',
            property_type='LAND',
            category=self.category,
            location='Dar es Salaam',
            price=1000000,
            size=100,
            bedrooms=0,
            bathrooms=0,
            seller=self.seller
        )
        self.assertEqual(listing.title, 'Test Property')
        self.assertEqual(listing.status, 'PENDING')
        self.assertIsNotNone(listing.listing_id)
        self.assertEqual(listing.seller, self.seller)
    
    def test_listing_str_method(self):
        """Test the string representation"""
        listing = Listing.objects.create(
            title='Test Property',
            description='Beautiful land for sale',
            property_type='LAND',
            category=self.category,
            location='Dar es Salaam',
            price=1000000,
            size=100,
            seller=self.seller
        )
        self.assertIn(listing.title, str(listing))
    
    def test_increment_view_count(self):
        """Test incrementing view count"""
        listing = Listing.objects.create(
            title='Test Property',
            description='Beautiful land for sale',
            property_type='LAND',
            category=self.category,
            location='Dar es Salaam',
            price=1000000,
            size=100,
            seller=self.seller
        )
        self.assertEqual(listing.view_count, 0)
        listing.increment_view_count()
        self.assertEqual(listing.view_count, 1)

class ListingAPITest(APITestCase):
    """Test Listing API endpoints"""
    
    def setUp(self):
        self.seller = User.objects.create_user(
            username='seller',
            email='seller@test.com',
            password='SellerPass123!',
            phone_number='0712345678',
            role='DALALI',
            is_verified=True
        )
        
        self.buyer = User.objects.create_user(
            username='buyer',
            email='buyer@test.com',
            password='BuyerPass123!',
            phone_number='0712345679',
            role='MTEJA'
        )
        
        self.category = Category.objects.create(
            name='Land',
            description='Land properties'
        )
        
        self.listing = Listing.objects.create(
            title='Test Property',
            description='Beautiful land for sale',
            property_type='LAND',
            category=self.category,
            location='Dar es Salaam',
            price=1000000,
            size=100,
            seller=self.seller,
            status='ACTIVE'
        )
    
    def test_list_listings(self):
        """Test listing all listings"""
        url = reverse('listings-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_listing(self):
        """Test creating a listing via API"""
        self.client.force_authenticate(user=self.seller)
        url = reverse('listings-list')
        data = {
            'title': 'New Property',
            'description': 'Nice property',
            'property_type': 'HOUSE',
            'category': self.category.id,
            'location': 'Dodoma',
            'price': 500000,
            'size': 200,
            'bedrooms': 3,
            'bathrooms': 2
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'PENDING')
    
    def test_get_listing_detail(self):
        """Test getting listing detail"""
        url = reverse('listings-detail', kwargs={'pk': self.listing.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.listing.id)
    
    def test_search_listings(self):
        """Test searching listings"""
        url = reverse('listings-search')
        response = self.client.get(url, {'q': 'Test', 'property_type': 'LAND'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_filter_by_price(self):
        """Test filtering listings by price"""
        url = reverse('listings-list')
        response = self.client.get(url, {'min_price': 500000, 'max_price': 1500000})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include our listing
        self.assertGreaterEqual(len(response.data['results']), 1)