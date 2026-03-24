"""
User repository for database operations related to User model.
"""
from typing import List, Optional, Dict, Any
from django.db.models import Q
from core.models import User, UserType
from .base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository for User model with specific user-related operations.
    """
    
    def __init__(self):
        super().__init__(User)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None
    
    def get_active_users(self) -> List[User]:
        """Get all active users."""
        return list(User.objects.filter(is_active=True))
    
    def get_users_by_type(self, user_type: str) -> List[User]:
        """Get users by type."""
        return list(User.objects.filter(user_type=user_type, is_active=True))
    
    def get_admins(self) -> List[User]:
        """Get all admin users."""
        return self.get_users_by_type(UserType.ADMIN.value)
    
    def get_super_users(self) -> List[User]:
        """Get all super users."""
        return self.get_users_by_type(UserType.SUPER_USER.value)
    
    def get_super_workspace_users(self) -> List[User]:
        """Get all super workspace users."""
        return self.get_users_by_type(UserType.SUPER_WORKSPACE_USER.value)
    
    def get_regular_users(self) -> List[User]:
        """Get all regular users."""
        return self.get_users_by_type(UserType.USER.value)
    
    def create_user(self, email: str, username: str, password: str, 
                    user_type: str = UserType.USER.value, **extra_fields) -> User:
        """Create a new user with hashed password."""
        return User.objects.create_user(
            email=email,
            username=username,
            password=password,
            user_type=user_type,
            **extra_fields
        )
    
    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user information."""
        user = self.get_by_id(user_id)
        if user:
            # Handle password separately
            password = kwargs.pop('password', None)
            for key, value in kwargs.items():
                setattr(user, key, value)
            if password:
                user.set_password(password)
            user.save()
            return user
        return None
    
    def deactivate_user(self, user_id: int) -> Optional[User]:
        """Deactivate a user account."""
        return self.update_user(user_id, is_active=False)
    
    def activate_user(self, user_id: int) -> Optional[User]:
        """Activate a user account."""
        return self.update_user(user_id, is_active=True)
    
    def change_password(self, user_id: int, new_password: str) -> Optional[User]:
        """Change user password."""
        user = self.get_by_id(user_id)
        if user:
            user.set_password(new_password)
            user.save()
            return user
        return None
    
    def verify_password(self, email: str, password: str) -> Optional[User]:
        """Verify user credentials."""
        user = self.get_by_email(email)
        if user and user.check_password(password):
            return user
        return None
    
    def search_users(self, query: str) -> List[User]:
        """Search users by email, username, first name, or last name."""
        return list(User.objects.filter(
            Q(email__icontains=query) |
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query),
            is_active=True
        ))
    
    def get_users_count_by_type(self) -> Dict[str, int]:
        """Get count of users by type."""
        from django.db.models import Count
        result = User.objects.values('user_type').annotate(count=Count('id'))
        return {item['user_type']: item['count'] for item in result}
    
    def email_exists(self, email: str) -> bool:
        """Check if email already exists."""
        return User.objects.filter(email=email).exists()
    
    def username_exists(self, username: str) -> bool:
        """Check if username already exists."""
        return User.objects.filter(username=username).exists()
