"""
User service for business logic related to User model.
"""
from typing import List, Optional, Dict, Any
from core.models import User, UserType
from core.repositories import UserRepository


class UserService:
    """
    Service for User-related business logic.
    """
    
    def __init__(self):
        self.user_repository = UserRepository()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.user_repository.get_by_id(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.user_repository.get_by_email(email)
    
    def get_all_users(self) -> List[User]:
        """Get all users."""
        return self.user_repository.get_all()
    
    def get_active_users(self) -> List[User]:
        """Get all active users."""
        return self.user_repository.get_active_users()
    
    def get_users_by_type(self, user_type: str) -> List[User]:
        """Get users by type."""
        return self.user_repository.get_users_by_type(user_type)
    
    def create_user(self, email: str, username: str, password: str,
                    user_type: str = UserType.USER.value,
                    first_name: str = '',
                    last_name: str = '',
                    **extra_fields) -> User:
        """
        Create a new user.
        
        Args:
            email: User's email address
            username: Unique username
            password: User's password
            user_type: Type of user (admin, super_user, super_group_user, user)
            first_name: User's first name
            last_name: User's last name
            **extra_fields: Additional fields
        
        Returns:
            Created User instance
        
        Raises:
            ValueError: If email or username already exists
        """
        # Validate email uniqueness
        if self.user_repository.email_exists(email):
            raise ValueError(f"User with email '{email}' already exists")
        
        # Validate username uniqueness
        if self.user_repository.username_exists(username):
            raise ValueError(f"Username '{username}' is already taken")
        
        return self.user_repository.create_user(
            email=email,
            username=username,
            password=password,
            user_type=user_type,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
    
    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user information."""
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Check email uniqueness if changing email
        if 'email' in kwargs and kwargs['email'] != user.email:
            if self.user_repository.email_exists(kwargs['email']):
                raise ValueError(f"Email '{kwargs['email']}' is already in use")
        
        # Check username uniqueness if changing username
        if 'username' in kwargs and kwargs['username'] != user.username:
            if self.user_repository.username_exists(kwargs['username']):
                raise ValueError(f"Username '{kwargs['username']}' is already taken")
        
        return self.user_repository.update_user(user_id, **kwargs)
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user."""
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        return self.user_repository.delete(user_id)
    
    def deactivate_user(self, user_id: int) -> Optional[User]:
        """Deactivate a user account."""
        return self.user_repository.deactivate_user(user_id)
    
    def activate_user(self, user_id: int) -> Optional[User]:
        """Activate a user account."""
        return self.user_repository.activate_user(user_id)
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        Change user password.
        
        Args:
            user_id: User's ID
            old_password: Current password
            new_password: New password
        
        Returns:
            True if password changed successfully
        
        Raises:
            ValueError: If old password is incorrect or user not found
        """
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        if not user.check_password(old_password):
            raise ValueError("Incorrect current password")
        
        self.user_repository.change_password(user_id, new_password)
        return True
    
    def search_users(self, query: str) -> List[User]:
        """Search users by query string.
        
        Supports partial matching like Slack - searching for "a" will find
        all users containing "a" in their email, username, first name, or last name.
        """
        if not query:
            return []
        return self.user_repository.search_users(query)
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics."""
        return {
            'total_users': self.user_repository.count(),
            'active_users': self.user_repository.count(is_active=True),
            'users_by_type': self.user_repository.get_users_count_by_type(),
        }
    
    def get_admins(self) -> List[User]:
        """Get all admin users."""
        return self.user_repository.get_admins()
    
    def get_super_users(self) -> List[User]:
        """Get all super users."""
        return self.user_repository.get_super_users()
    
    def get_super_group_users(self) -> List[User]:
        """Get all super group users."""
        return self.user_repository.get_super_group_users()
    
    def get_regular_users(self) -> List[User]:
        """Get all regular users."""
        return self.user_repository.get_regular_users()
