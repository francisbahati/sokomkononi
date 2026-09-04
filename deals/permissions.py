from rest_framework import permissions


class IsDealParticipant(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (request.user == obj.buyer or
                request.user == obj.seller or
                request.user.role == 'ADMIN')


class IsDealBuyer(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.buyer


class IsDealSeller(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.seller


class CanUpdateDealStatus(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (request.user.role == 'ADMIN' or
                request.user == obj.buyer or
                request.user == obj.seller)