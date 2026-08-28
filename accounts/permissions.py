from rest_framework import permissions

class IsDalali(permissions.BasePermission):
    """Check if user is a Dalali"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'DALALI'

class IsMteja(permissions.BasePermission):
    """Check if user is a Mteja"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'MTEJA'

class IsAdmin(permissions.BasePermission):
    """Check if user is Admin"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'ADMIN'

class IsVerifiedDalali(permissions.BasePermission):
    """Dalali must be KYC verified"""
    def has_permission(self, request, view):
        return (request.user.is_authenticated and 
                request.user.role == 'DALALI' and 
                request.user.is_verified)