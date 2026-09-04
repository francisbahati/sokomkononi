from rest_framework import serializers
from .models import DealRoom, NegotiationMessage, DealDocument, DealActivity, Offer
from listings.serializers import ListingSerializer
from accounts.serializers import UserProfileSerializer


class OfferSerializer(serializers.ModelSerializer):
    made_by_details = UserProfileSerializer(source='made_by', read_only=True)

    class Meta:
        model = Offer
        fields = ['id', 'deal_room', 'made_by', 'made_by_details', 'amount',
                  'message', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'made_by', 'created_at', 'updated_at']


class OfferCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = ['deal_room', 'amount', 'message']

    def validate(self, attrs):
        deal = attrs.get('deal_room')
        user = self.context['request'].user
        if user not in [deal.buyer, deal.seller]:
            raise serializers.ValidationError("You are not a participant in this deal.")
        if deal.status not in [DealRoom.Status.NEGOTIATING, DealRoom.Status.AGREEMENT]:
            raise serializers.ValidationError("Cannot make offers at this stage.")
        return attrs


class NegotiationMessageSerializer(serializers.ModelSerializer):
    sender_details = UserProfileSerializer(source='sender', read_only=True)

    class Meta:
        model = NegotiationMessage
        fields = ['id', 'deal_room', 'sender', 'sender_details', 'message',
                  'is_offer', 'offer_amount', 'created_at']
        read_only_fields = ['id', 'sender', 'created_at']


class NegotiationMessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NegotiationMessage
        fields = ['deal_room', 'message', 'is_offer', 'offer_amount']

    def validate(self, attrs):
        if attrs.get('is_offer') and not attrs.get('offer_amount'):
            raise serializers.ValidationError(
                {"offer_amount": "Offer amount is required when making an offer"}
            )
        return attrs


class DealDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_details = UserProfileSerializer(source='uploaded_by', read_only=True)

    class Meta:
        model = DealDocument
        fields = ['id', 'deal_room', 'title', 'document_type', 'file',
                  'description', 'uploaded_by', 'uploaded_by_details', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_by', 'uploaded_at']


class DealActivitySerializer(serializers.ModelSerializer):
    user_details = UserProfileSerializer(source='user', read_only=True)

    class Meta:
        model = DealActivity
        fields = ['id', 'deal_room', 'user', 'user_details', 'action',
                  'details', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class DealRoomSerializer(serializers.ModelSerializer):
    listing_details = ListingSerializer(source='listing', read_only=True)
    buyer_details = UserProfileSerializer(source='buyer', read_only=True)
    seller_details = UserProfileSerializer(source='seller', read_only=True)
    messages = NegotiationMessageSerializer(many=True, read_only=True)
    documents = DealDocumentSerializer(many=True, read_only=True)
    activities = DealActivitySerializer(many=True, read_only=True)
    offers = OfferSerializer(many=True, read_only=True)

    class Meta:
        model = DealRoom
        fields = ['id', 'listing', 'listing_details', 'buyer', 'buyer_details',
                  'seller', 'seller_details', 'original_price', 'final_price',
                  'buyer_offer', 'seller_counter', 'status', 'commission_amount',
                  'messages', 'documents', 'activities', 'offers',
                  'created_at', 'updated_at', 'completed_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at']


class DealRoomCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DealRoom
        fields = ['listing', 'buyer', 'seller', 'original_price']

    def validate(self, attrs):
        if attrs.get('buyer') == attrs.get('seller'):
            raise serializers.ValidationError("Buyer and seller cannot be the same user")
        return attrs


class DealRoomUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DealRoom
        fields = ['status', 'final_price', 'buyer_offer', 'seller_counter',
                  'commission_amount', 'completed_at']

    def validate(self, attrs):
        if attrs.get('buyer_offer') and attrs.get('buyer_offer') <= 0:
            raise serializers.ValidationError({"buyer_offer": "Offer amount must be > 0"})
        if attrs.get('seller_counter') and attrs.get('seller_counter') <= 0:
            raise serializers.ValidationError({"seller_counter": "Counter offer must be > 0"})
        if attrs.get('final_price') and attrs.get('final_price') <= 0:
            raise serializers.ValidationError({"final_price": "Final price must be > 0"})
        return attrs


class DealActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=[
        ('ACCEPT', 'Accept'),
        ('REJECT', 'Reject'),
        ('COUNTER', 'Counter Offer'),
        ('COMPLETE', 'Complete'),
        ('CANCEL', 'Cancel'),
        ('DISPUTE', 'Dispute'),
    ])
    offer_id = serializers.IntegerField(required=False)   # for accepting a specific offer
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    message = serializers.CharField(required=False)

    def validate(self, attrs):
        if attrs.get('action') == 'ACCEPT':
            if not attrs.get('offer_id'):
                raise serializers.ValidationError({"offer_id": "Offer ID required to accept."})
        if attrs.get('action') == 'COUNTER':
            if not attrs.get('amount'):
                raise serializers.ValidationError({"amount": "Amount required for counter offer."})
        return attrs