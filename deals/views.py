from rest_framework import generics, status, permissions, viewsets, mixins, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import DealRoom, NegotiationMessage, DealDocument, DealActivity, Offer
from .serializers import (
    DealRoomSerializer,
    DealRoomCreateSerializer,
    DealRoomUpdateSerializer,
    NegotiationMessageSerializer,
    NegotiationMessageCreateSerializer,
    DealDocumentSerializer,
    DealActivitySerializer,
    DealActionSerializer,
    OfferSerializer,
    OfferCreateSerializer,
)
from .permissions import (
    IsDealParticipant,
    IsDealBuyer,
    IsDealSeller,
    CanUpdateDealStatus,
)


# ---------- Dummy serializer for schema ----------
class EmptySerializer(serializers.Serializer):
    pass


# ---------- Admin Deal List ----------
class AdminDealListView(generics.ListAPIView):
    """Admin endpoint for listing all deals with status filter."""
    serializer_class = DealRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Guard for schema generation
        if getattr(self, 'swagger_fake_view', False):
            return DealRoom.objects.none()
        # Only admin can access
        if self.request.user.role != 'ADMIN':
            return DealRoom.objects.none()
        queryset = DealRoom.objects.all()
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-created_at')


# ---------- Offer Views ----------
class OfferViewSet(viewsets.ModelViewSet):
    """ViewSet for managing offers."""
    queryset = Offer.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsDealParticipant]

    def get_serializer_class(self):
        if self.action == 'create':
            return OfferCreateSerializer
        return OfferSerializer

    def get_queryset(self):
        # Filter by deal room if provided in URL
        deal_pk = self.kwargs.get('deal_pk')
        if deal_pk:
            return Offer.objects.filter(deal_room_id=deal_pk)
        return Offer.objects.none()

    def perform_create(self, serializer):
        deal_room_id = self.kwargs.get('deal_pk')
        deal_room = get_object_or_404(DealRoom, id=deal_room_id)
        serializer.save(deal_room=deal_room, made_by=self.request.user)
        # Also create a message for the offer
        NegotiationMessage.objects.create(
            deal_room=deal_room,
            sender=self.request.user,
            message=serializer.validated_data.get('message', 'Offer made'),
            is_offer=True,
            offer_amount=serializer.validated_data['amount']
        )
        # Update deal room's buyer_offer or seller_counter
        if self.request.user == deal_room.buyer:
            deal_room.buyer_offer = serializer.validated_data['amount']
        elif self.request.user == deal_room.seller:
            deal_room.seller_counter = serializer.validated_data['amount']
        deal_room.save()

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        offer = self.get_object()
        if offer.status != Offer.Status.PENDING:
            return Response({'error': 'Offer already processed.'}, status=status.HTTP_400_BAD_REQUEST)
        if request.user not in [offer.deal_room.buyer, offer.deal_room.seller]:
            return Response({'error': 'You are not a participant.'}, status=status.HTTP_403_FORBIDDEN)
        offer.accept()
        return Response(OfferSerializer(offer).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        offer = self.get_object()
        if offer.status != Offer.Status.PENDING:
            return Response({'error': 'Offer already processed.'}, status=status.HTTP_400_BAD_REQUEST)
        offer.reject()
        return Response(OfferSerializer(offer).data)


# ---------- DealRoom ViewSet ----------
class DealRoomViewSet(viewsets.ModelViewSet):
    queryset = DealRoom.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return DealRoomCreateSerializer
        elif self.action in ['update', 'partial_update', 'update_status']:
            return DealRoomUpdateSerializer
        return DealRoomSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            queryset = DealRoom.objects.all()
        else:
            queryset = DealRoom.objects.filter(Q(buyer=user) | Q(seller=user))
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def perform_create(self, serializer):
        deal = serializer.save()
        DealActivity.objects.create(
            deal_room=deal,
            user=self.request.user,
            action='MESSAGE',
            details={'message': 'Deal room created'}
        )

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        deal = self.get_object()
        if request.user.role != 'ADMIN' and request.user not in [deal.buyer, deal.seller]:
            return Response({'error': 'No permission.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(deal, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        old_status = deal.status
        deal = serializer.save()
        DealActivity.objects.create(
            deal_room=deal,
            user=request.user,
            action='COMPLETE' if deal.status == 'COMPLETED' else 'CANCEL',
            details={'old_status': old_status, 'new_status': deal.status}
        )
        return Response(DealRoomSerializer(deal).data)


# ---------- Other Views ----------
class NegotiationMessageViewSet(viewsets.ModelViewSet):
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
        message = serializer.save(deal_room=deal_room, sender=self.request.user)
        if message.is_offer:
            if self.request.user == deal_room.buyer:
                deal_room.buyer_offer = message.offer_amount
            elif self.request.user == deal_room.seller:
                deal_room.seller_counter = message.offer_amount
            deal_room.save()
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
        document = serializer.save(deal_room=deal_room, uploaded_by=self.request.user)
        DealActivity.objects.create(
            deal_room=deal_room,
            user=self.request.user,
            action='MESSAGE',
            details={'message': f'Document uploaded: {document.title}'}
        )


class DealActivityViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = DealActivity.objects.all()
    serializer_class = DealActivitySerializer
    permission_classes = [permissions.IsAuthenticated, IsDealParticipant]

    def get_queryset(self):
        deal_pk = self.kwargs.get('pk')
        if deal_pk:
            return DealActivity.objects.filter(deal_room_id=deal_pk)
        return DealActivity.objects.none()


class DealActionView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsDealParticipant]
    serializer_class = DealActionSerializer

    def post(self, request, pk=None):
        deal = get_object_or_404(DealRoom, id=pk)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']
        offer_id = serializer.validated_data.get('offer_id')
        amount = serializer.validated_data.get('amount')
        message = serializer.validated_data.get('message', '')

        # Handle actions
        if action == 'ACCEPT':
            offer = get_object_or_404(Offer, id=offer_id, deal_room=deal)
            if offer.status != Offer.Status.PENDING:
                return Response({'error': 'Offer already processed.'}, status=status.HTTP_400_BAD_REQUEST)
            offer.accept()
            DealActivity.objects.create(
                deal_room=deal,
                user=request.user,
                action='ACCEPT',
                details={'offer_id': offer.id, 'amount': str(offer.amount), 'message': message}
            )
            return Response({'status': 'Offer accepted', 'deal': DealRoomSerializer(deal).data})

        elif action == 'REJECT':
            if offer_id:
                offer = get_object_or_404(Offer, id=offer_id, deal_room=deal)
                offer.reject()
                DealActivity.objects.create(
                    deal_room=deal,
                    user=request.user,
                    action='REJECT',
                    details={'offer_id': offer.id, 'message': message}
                )
                return Response({'status': 'Offer rejected'})
            else:
                DealActivity.objects.create(
                    deal_room=deal,
                    user=request.user,
                    action='REJECT',
                    details={'message': message}
                )
                return Response({'status': 'Rejected'})

        elif action == 'COUNTER':
            if not amount:
                return Response({'error': 'Amount required for counter offer.'}, status=status.HTTP_400_BAD_REQUEST)
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
            Offer.objects.create(
                deal_room=deal,
                made_by=request.user,
                amount=amount,
                message=message,
                status=Offer.Status.PENDING
            )
            return Response({'status': 'Counter offer made', 'deal': DealRoomSerializer(deal).data})

        elif action == 'COMPLETE':
            deal.mark_as_completed()
            DealActivity.objects.create(
                deal_room=deal,
                user=request.user,
                action='COMPLETE',
                details={'message': message}
            )
            return Response({'status': 'Deal completed', 'deal': DealRoomSerializer(deal).data})

        elif action == 'CANCEL':
            deal.mark_as_cancelled()
            DealActivity.objects.create(
                deal_room=deal,
                user=request.user,
                action='CANCEL',
                details={'message': message}
            )
            return Response({'status': 'Deal cancelled', 'deal': DealRoomSerializer(deal).data})

        elif action == 'DISPUTE':
            deal.mark_as_disputed()
            DealActivity.objects.create(
                deal_room=deal,
                user=request.user,
                action='DISPUTE',
                details={'message': message}
            )
            return Response({'status': 'Dispute raised', 'deal': DealRoomSerializer(deal).data})

        return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)


class MyDealsView(generics.ListAPIView):
    serializer_class = DealRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Guard for schema generation
        if getattr(self, 'swagger_fake_view', False):
            return DealRoom.objects.none()
        user = self.request.user
        return DealRoom.objects.filter(Q(buyer=user) | Q(seller=user)).order_by('-created_at')