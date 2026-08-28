from rest_framework import permissions

class IsPaymentParticipant(permissions.BasePermission):
    """Check if user is a participant in the payment"""
    def has_object_permission(self, request, view, obj):
        return (request.user == obj.buyer or 
                request.user == obj.seller or 
                request.user.role == 'ADMIN')

class IsPaymentBuyer(permissions.BasePermission):
    """Check if user is the buyer in the payment"""
    def has_object_permission(self, request, view, obj):
        return request.user == obj.buyer

class IsPaymentSeller(permissions.BasePermission):
    """Check if user is the seller in the payment"""
    def has_object_permission(self, request, view, obj):
        return request.user == obj.seller

class CanProcessPayment(permissions.BasePermission):
    """Check if user can process payments"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'ADMIN'