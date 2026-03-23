"""
Authentication service for login, logout, and token management.
"""
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.http import HttpRequest
from core.models import User, UserType
from core.repositories import UserRepository


class AuthService:
    """
    Service for authentication-related business logic.
    """
    
    # JWT settings
    JWT_SECRET = settings.SECRET_KEY
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = 24
    
    def __init__(self):
        self.user_repository = UserRepository()
    
    def login(self, request: HttpRequest, email: str, password: str) -> Optional[User]:
        """
        Authenticate user and create session.
        
        Args:
            request: HTTP request object
            email: User's email address
            password: User's password
        
        Returns:
            User instance if authentication successful, None otherwise
        """
        user = authenticate(request, username=email, password=password)
        if user and user.is_active:
            login(request, user)
            return user
        return None
    
    def logout(self, request: HttpRequest) -> None:
        """
        Log out user by ending session.
        
        Args:
            request: HTTP request object
        """
        logout(request)
    
    def verify_credentials(self, email: str, password: str) -> Optional[User]:
        """
        Verify user credentials without creating session.
        
        Args:
            email: User's email address
            password: User's password
        
        Returns:
            User instance if credentials valid, None otherwise
        """
        return self.user_repository.verify_password(email, password)
    
    def generate_jwt_token(self, user: User) -> str:
        """
        Generate JWT token for user.
        
        Args:
            user: User instance
        
        Returns:
            JWT token string
        """
        payload = {
            'user_id': user.id,
            'email': user.email,
            'username': user.username,
            'user_type': user.user_type,
            'exp': datetime.utcnow() + timedelta(hours=self.JWT_EXPIRATION_HOURS),
            'iat': datetime.utcnow(),
        }
        return jwt.encode(payload, self.JWT_SECRET, algorithm=self.JWT_ALGORITHM)
    
    def decode_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode and validate JWT token.
        
        Args:
            token: JWT token string
        
        Returns:
            Decoded payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.JWT_SECRET, algorithms=[self.JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def get_user_from_token(self, token: str) -> Optional[User]:
        """
        Get user from JWT token.
        
        Args:
            token: JWT token string
        
        Returns:
            User instance if token valid, None otherwise
        """
        payload = self.decode_jwt_token(token)
        if payload:
            return self.user_repository.get_by_id(payload.get('user_id'))
        return None
    
    def refresh_token(self, token: str) -> Optional[str]:
        """
        Refresh JWT token.
        
        Args:
            token: Current JWT token
        
        Returns:
            New JWT token if valid, None otherwise
        """
        user = self.get_user_from_token(token)
        if user and user.is_active:
            return self.generate_jwt_token(user)
        return None
    
    def register_user(self, email: str, username: str, password: str,
                      user_type: str = UserType.USER.value,
                      first_name: str = '',
                      last_name: str = '',
                      **extra_fields) -> User:
        """
        Register a new user.
        
        Args:
            email: User's email address
            username: Unique username
            password: User's password
            user_type: Type of user
            first_name: User's first name
            last_name: User's last name
            **extra_fields: Additional fields
        
        Returns:
            Created User instance
        
        Raises:
            ValueError: If validation fails
        """
        # Check if email already exists
        if self.user_repository.email_exists(email):
            raise ValueError(f"User with email '{email}' already exists")
        
        # Check if username already exists
        if self.user_repository.username_exists(username):
            raise ValueError(f"Username '{username}' is already taken")
        
        # Create user
        user = self.user_repository.create_user(
            email=email,
            username=username,
            password=password,
            user_type=user_type,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
        
        return user
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        Change user password with verification.
        
        Args:
            user_id: User's ID
            old_password: Current password
            new_password: New password
        
        Returns:
            True if password changed successfully
        """
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        if not user.check_password(old_password):
            raise ValueError("Incorrect current password")
        
        self.user_repository.change_password(user_id, new_password)
        return True
    
    def request_password_reset(self, email: str) -> Optional[str]:
        """
        Request password reset token.
        
        Args:
            email: User's email address
        
        Returns:
            Reset token if user exists, None otherwise
        """
        user = self.user_repository.get_by_email(email)
        if user:
            # Generate a reset token valid for 1 hour
            payload = {
                'user_id': user.id,
                'action': 'password_reset',
                'exp': datetime.utcnow() + timedelta(hours=1),
                'iat': datetime.utcnow(),
            }
            return jwt.encode(payload, self.JWT_SECRET, algorithm=self.JWT_ALGORITHM)
        return None
    
    def reset_password(self, token: str, new_password: str) -> bool:
        """
        Reset password using reset token.
        
        Args:
            token: Password reset token
            new_password: New password
        
        Returns:
            True if password reset successful
        """
        payload = self.decode_jwt_token(token)
        if not payload or payload.get('action') != 'password_reset':
            raise ValueError("Invalid or expired reset token")
        
        user_id = payload.get('user_id')
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        self.user_repository.change_password(user_id, new_password)
        return True
