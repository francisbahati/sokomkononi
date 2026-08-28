from rest_framework import permissions

class IsPlatformAdmin(permissions.BasePermission):
    """Check if user is a platform admin"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'ADMIN'
    
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and request.user.role == 'ADMIN'

class CanManageDisputes(permissions.BasePermission):
    """Check if user can manage disputes"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'ADMIN'
    
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and request.user.role == 'ADMIN'

class CanViewAuditLogs(permissions.BasePermission):
    """Check if user can view audit logs"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'ADMIN'