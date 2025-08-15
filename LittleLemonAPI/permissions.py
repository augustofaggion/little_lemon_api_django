from rest_framework.permissions import BasePermission, SAFE_METHODS

def in_group(user, name):
    return user and user.is_authenticated and user.groups.filter(name=name).exists()

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)

class IsManager(BasePermission):
    def has_permission(self, request, view):
        return bool(in_group(request.user, "Manager") or request.user.is_staff)

class IsDeliveryCrew(BasePermission):
    def has_permission(self, request, view):
        return bool(in_group(request.user, "Delivery crew") or request.user.is_staff)

class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS
