from rest_framework import permissions

class IsNotificationOwner(permissions.BasePermission):
    """Check if user owns the notification"""
    def has_object_permission(self, request, view, obj):
        return request.user == obj.user

class CanManageNotifications(permissions.BasePermission):
    """Check if user can manage notifications (admin)"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'ADMIN'