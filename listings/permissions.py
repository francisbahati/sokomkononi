from rest_framework import permissions


class IsListingOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.seller


class IsVerifiedDalali(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user.is_authenticated and
                request.user.role == 'DALALI' and
                request.user.is_verified)


class CanManageListing(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (request.user.role == 'ADMIN' or
                request.user == obj.seller)


class CanViewListing(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.status in ['ACTIVE', 'VERIFIED']:
            return True
        return request.user == obj.seller