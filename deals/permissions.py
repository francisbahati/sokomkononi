from rest_framework import permissions

class IsDealParticipant(permissions.BasePermission):
    """Check if user is a participant in the deal"""
    def has_object_permission(self, request, view, obj):
        return (request.user == obj.buyer or 
                request.user == obj.seller or 
                request.user.role == 'ADMIN')

class IsDealBuyer(permissions.BasePermission):
    """Check if user is the buyer in the deal"""
    def has_object_permission(self, request, view, obj):
        return request.user == obj.buyer

class IsDealSeller(permissions.BasePermission):
    """Check if user is the seller in the deal"""
    def has_object_permission(self, request, view, obj):
        return request.user == obj.seller

class CanUpdateDealStatus(permissions.BasePermission):
    """Check if user can update deal status"""
    def has_object_permission(self, request, view, obj):
        # Only admin or both parties can update status
        return (request.user.role == 'ADMIN' or 
                request.user == obj.buyer or 
                request.user == obj.seller)