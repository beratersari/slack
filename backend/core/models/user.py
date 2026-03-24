"""
User model for authentication and authorization.
"""
from enum import Enum
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from .base import BaseModel

# Threshold for considering a user "online" (in minutes)
ONLINE_THRESHOLD_MINUTES = 5


class UserType(Enum):
    """
    Enum for user types in the system.
    """
    ADMIN = 'admin'
    SUPER_USER = 'super_user'
    SUPER_WORKSPACE_USER = 'super_workspace_user'
    USER = 'user'

    @classmethod
    def choices(cls):
        return [(tag.value, tag.name.replace('_', ' ').title()) for tag in cls]


class UserManager(BaseUserManager):
    """
    Custom user manager for User model.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', UserType.ADMIN.value)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

    def get_by_email(self, email):
        """Get user by email address."""
        try:
            return self.get(email=email)
        except self.model.DoesNotExist:
            return None

    def get_active_users(self):
        """Get all active users."""
        return self.filter(is_active=True)

    def get_users_by_type(self, user_type):
        """Get users by type."""
        return self.filter(user_type=user_type, is_active=True)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """
    Custom User model with multiple user types.
    
    User Types:
    - Admin: Full system access, can manage all users and settings
    - Super User: Can manage multiple workspaces and users
    - Super Workspace User: Can manage a single workspace
    - User: Regular user with basic access
    """
    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    
    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices(),
        default=UserType.USER.value,
        db_index=True
    )
    
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Profile information
    avatar = models.URLField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    
    # Status
    status_message = models.CharField(max_length=200, blank=True, null=True)
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Presence tracking (like Slack)
    last_seen = models.DateTimeField(null=True, blank=True, db_index=True)
    
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['user_type']),
        ]

    def __str__(self):
        return f"{self.email} ({self.get_user_type_display()})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def is_admin(self):
        return self.user_type == UserType.ADMIN.value

    def is_super_user_type(self):
        return self.user_type == UserType.SUPER_USER.value

    def is_super_workspace_user(self):
        return self.user_type == UserType.SUPER_WORKSPACE_USER.value

    def is_regular_user(self):
        return self.user_type == UserType.USER.value

    # --- Presence methods (like Slack) ---

    def update_last_seen(self):
        """Update last_seen timestamp to now. Call this on user activity."""
        self.last_seen = timezone.now()
        self.save(update_fields=['last_seen'])

    @property
    def is_online(self):
        """
        Check if user is currently online (active within threshold).
        Returns False if user is inactive or has no last_seen.
        """
        if not self.is_active:
            return False
        if not self.last_seen:
            return False
        threshold = timedelta(minutes=ONLINE_THRESHOLD_MINUTES)
        return timezone.now() - self.last_seen <= threshold

    @property
    def presence_display(self):
        """
        Get human-readable presence string like Slack.
        Returns: 'Active', 'Away', 'Offline', or 'Inactive'
        """
        if not self.is_active:
            return 'Inactive'
        if not self.last_seen:
            return 'Offline'
        if self.is_online:
            return 'Active'
        # Calculate time since last seen
        delta = timezone.now() - self.last_seen
        minutes = int(delta.total_seconds() / 60)
        if minutes < 60:
            return f'Last seen {minutes} min ago'
        hours = int(minutes / 60)
        if hours < 24:
            return f'Last seen {hours} hour{"s" if hours > 1 else ""} ago'
        days = int(hours / 24)
        return f'Last seen {days} day{"s" if days > 1 else ""} ago'
