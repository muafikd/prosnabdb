from rest_framework import permissions


class IsManagerOrAdmin(permissions.BasePermission):
    """
    Permission class that allows access only to users with roles:
    - Администратор (Administrator)
    - Менеджер (Manager)
    
    Users with role Просмотр (Viewer) are denied access.
    """
    
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has allowed role
        allowed_roles = ['Администратор', 'Менеджер']
        return request.user.user_role in allowed_roles

