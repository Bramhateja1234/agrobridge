"""Custom permission classes for AgroBridge."""
from rest_framework.permissions import BasePermission


class IsFarmer(BasePermission):
    """Allow access only to farmers."""
    message = 'Only farmers can perform this action.'

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and
            (request.user.role == 'farmer' or request.user.role == 'admin' or request.user.is_superuser)
        )


class IsConsumer(BasePermission):
    """Allow access only to consumers."""
    message = 'Only consumers can perform this action.'

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and
            (request.user.role == 'consumer' or request.user.role == 'admin' or request.user.is_superuser)
        )


class IsAdminUser(BasePermission):
    """Allow access only to admins."""
    message = 'Only admins can perform this action.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and
                    (request.user.role == 'admin' or request.user.is_superuser))


class IsDeliveryAgent(BasePermission):
    """Allow access only to delivery agents."""
    message = 'Only delivery agents can perform this action.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and
                    (request.user.role == 'delivery' or request.user.role == 'admin' or request.user.is_superuser))


class IsFarmerOrReadOnly(BasePermission):
    """Farmers can write; anyone can read."""
    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return bool(request.user and request.user.is_authenticated and request.user.role == 'farmer')


class IsOwnerOrAdmin(BasePermission):
    """Allow only the owner or admin."""
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin' or request.user.is_superuser:
            return True
        return obj == request.user or getattr(obj, 'consumer', None) == request.user or \
               getattr(obj, 'farmer', None) == request.user
