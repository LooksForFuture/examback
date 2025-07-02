from rest_framework import permissions

class IsSuperUser(permissions.BasePermission):
    """
    Permission to grant access only to superuser accounts.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated and is a superuser
        return request.user and request.user.is_authenticated and request.user.is_superuser
