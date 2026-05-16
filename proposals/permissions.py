from rest_framework import permissions


class IsManagerOrAdmin(permissions.BasePermission):
    """
    Permission class that allows access only to users with roles:
    - Администратор (Administrator)
    - Менеджер (Manager)
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        allowed_roles = ['Администратор', 'Менеджер']
        return request.user.user_role in allowed_roles


class IsJuniorManager(permissions.BasePermission):
    """Allows access to 'Младший менеджер'."""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_role == 'Младший менеджер'


class IsAtLeastJuniorManager(permissions.BasePermission):
    """Allows access to Junior Manager, Manager and Admin."""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        allowed_roles = ['Администратор', 'Менеджер', 'Младший менеджер']
        return request.user.user_role in allowed_roles


class IsProposalOwnerOrAbove(permissions.BasePermission):
    """
    Allows Admin/Manager always.
    Allows Junior Manager only if they are the owner of the proposal.
    """
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Admin and Manager have full access
        if request.user.user_role in ['Администратор', 'Менеджер']:
            return True
            
        # Junior Manager can only edit/delete their own proposals
        if request.user.user_role == 'Младший менеджер':
            # Handle both CommercialProposal and related objects if needed
            owner = getattr(obj, 'user', None)
            if owner and owner.user_id == request.user.user_id:
                return True
            
        return False


class IsAdmin(permissions.BasePermission):
    """Allows access only to users with role 'Администратор'."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_role == 'Администратор'


class IsSuperuser(permissions.BasePermission):
    """Allows access only to superuser (is_superuser=True)."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(request.user, 'is_superuser', False)

