from rest_framework import generics, status, permissions, viewsets, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from django.utils import timezone
from .models import DealRoom, NegotiationMessage, DealDocument, DealActivity
from .serializers import (
    DealRoomSerializer,
    DealRoomCreateSerializer,
    DealRoomUpdateSerializer,
    NegotiationMessageSerializer,
    NegotiationMessageCreateSerializer,
    DealDocumentSerializer,
    DealActivitySerializer,
    DealActionSerializer
)
from .permissions import (
    IsDealParticipant,
    IsDealBuyer,
    IsDealSeller,
    CanUpdateDealStatus
)

class DealRoomViewSet(viewsets.ModelViewSet):
    """ViewSet for Deal Rooms"""
    queryset = DealRoom.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DealRoomCreateSerializer
        elif self.action in ['update', 'partial_update', 'update_status']:
            return DealRoomUpdateSerializer
        return DealRoomSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Users can only see deals they are involved in
        if user.role != 'ADMIN':
            queryset = queryset.filter(
                Q(buyer=user) | Q(seller=user)
            )
        
        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
    
    def perform_create(self, serializer):
        deal = serializer.save()
        # Log the creation
        DealActivity.objects.create(
            deal_room=deal,
            user=self.request.user,
            action='MESSAGE',
            details={'message': 'Deal room created'}
        )
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update deal status"""
        deal = self.get_object()
        
        # Check permission
        if request.user.role != 'ADMIN' and request.user not in [deal.buyer, deal.seller]:
            return Response(
                {'error': 'You do not have permission to update this deal'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(deal, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Log the status change
        old_status = deal.status
        deal = serializer.save()
        
        DealActivity.objects.create(
            deal_room=deal,
            user=request.user,
            action='COMPLETE' if deal.status == 'COMPLETED' else 'CANCEL',
            details={'old_status': old_status, 'new_status': deal.status}
        )
        
        return Response(DealRoomSerializer(deal).data)

class NegotiationMessageViewSet(viewsets.ModelViewSet):
    """ViewSet for negotiation messages"""
    queryset = NegotiationMessage.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsDealParticipant]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return NegotiationMessageCreateSerializer
        return NegotiationMessageSerializer
    
    def get_queryset(self):
        deal_pk = self.kwargs.get('pk')
        if deal_pk:
            return NegotiationMessage.objects.filter(deal_room_id=deal_pk)
        return NegotiationMessage.objects.none()
    
    def perform_create(self, serializer):
        deal_room_id = self.kwargs.get('pk')
        deal_room = DealRoom.objects.get(id=deal_room_id)
        
        message = serializer.save(
            deal_room=deal_room,
            sender=self.request.user
        )
        
        # If this is an offer, update the deal room
        if message.is_offer:
            if self.request.user == deal_room.buyer:
                deal_room.buyer_offer = message.offer_amount
            elif self.request.user == deal_room.seller:
                deal_room.seller_counter = message.offer_amount
            deal_room.save()
        
        # Log the message
        DealActivity.objects.create(
            deal_room=deal_room,
            user=self.request.user,
            action='OFFER' if message.is_offer else 'MESSAGE',
            details={
                'message': message.message,
                'offer_amount': str(message.offer_amount) if message.is_offer else None
            }
        )

class DealDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for deal documents"""
    queryset = DealDocument.objects.all()
    serializer_class = DealDocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsDealParticipant]
    
    def get_queryset(self):
        deal_pk = self.kwargs.get('pk')
        if deal_pk:
            return DealDocument.objects.filter(deal_room_id=deal_pk)
        return DealDocument.objects.none()
    
    def perform_create(self, serializer):
        deal_room_id = self.kwargs.get('pk')
        deal_room = DealRoom.objects.get(id=deal_room_id)
        
        document = serializer.save(
            deal_room=deal_room,
            uploaded_by=self.request.user
        )
        
        DealActivity.objects.create(
            deal_room=deal_room,
            user=self.request.user,
            action='MESSAGE',
            details={'message': f'Document uploaded: {document.title}'}
        )

class DealActivityViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """ViewSet for deal activities"""
    queryset = DealActivity.objects.all()
    serializer_class = DealActivitySerializer
    permission_classes = [permissions.IsAuthenticated, IsDealParticipant]
    
    def get_queryset(self):
        deal_pk = self.kwargs.get('pk')
        if deal_pk:
            return DealActivity.objects.filter(deal_room_id=deal_pk)
        return DealActivity.objects.none()

class DealActionView(generics.GenericAPIView):
    """Handle deal actions (accept, reject, counter, complete, cancel, dispute)"""
    permission_classes = [permissions.IsAuthenticated, IsDealParticipant]
    serializer_class = DealActionSerializer
    
    def post(self, request, pk=None):
        deal = DealRoom.objects.get(id=pk)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action = serializer.validated_data['action']
        amount = serializer.validated_data.get('amount')
        message = serializer.validated_data.get('message', '')
        
        # Process the action
        if action == 'ACCEPT':
            deal.status = DealRoom.Status.AGREEMENT
            deal.final_price = deal.buyer_offer or deal.seller_counter or deal.original_price
            deal.save()
            DealActivity.objects.create(
                deal_room=deal,
                user=request.user,
                action='ACCEPT',
                details={'message': message, 'accepted_price': str(deal.final_price)}
            )
            
        elif action == 'REJECT':
            DealActivity.objects.create(
                deal_room=deal,
                user=request.user,
                action='REJECT',
                details={'message': message}
            )
            
        elif action == 'COUNTER':
            if not amount:
                return Response(
                    {'error': 'Amount required for counter offer'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if request.user == deal.buyer:
                deal.buyer_offer = amount
            elif request.user == deal.seller:
                deal.seller_counter = amount
            deal.save()
            DealActivity.objects.create(
                deal_room=deal,
                user=request.user,
                action='COUNTER',
                details={'amount': str(amount), 'message': message}
            )
            
        elif action == 'COMPLETE':
            deal.mark_as_completed()
            DealActivity.objects.create(
                deal_room=deal,
                user=request.user,
                action='COMPLETE',
                details={'message': message}
            )
            
        elif action == 'CANCEL':
            deal.mark_as_cancelled()
            DealActivity.objects.create(
                deal_room=deal,
                user=request.user,
                action='CANCEL',
                details={'message': message}
            )
            
        elif action == 'DISPUTE':
            deal.mark_as_disputed()
            DealActivity.objects.create(
                deal_room=deal,
                user=request.user,
                action='DISPUTE',
                details={'message': message}
            )
        
        return Response({
            'status': 'success',
            'action': action,
            'deal': DealRoomSerializer(deal).data
        })

class MyDealsView(generics.ListAPIView):
    """Get all deals for the current user"""
    serializer_class = DealRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return DealRoom.objects.filter(
            Q(buyer=user) | Q(seller=user)
        ).order_by('-created_at')