"""
Group model for workspace/organization management.
"""
from enum import Enum
from django.db import models
from django.conf import settings
from .base import BaseModel


class GroupRole(Enum):
    """
    Enum for group member roles.
    """
    OWNER = 'owner'
    ADMIN = 'admin'
    MEMBER = 'member'
    GUEST = 'guest'

    @classmethod
    def choices(cls):
        return [(tag.value, tag.name.title()) for tag in cls]


class Group(BaseModel):
    """
    Group model representing a workspace/organization.
    
    Groups are the top-level organizational unit in the Slack clone.
    Users can be members of multiple groups.
    """
    name = models.CharField(max_length=100, db_index=True)
    description = models.TextField(blank=True, null=True)
    icon = models.URLField(blank=True, null=True)
    
    # Owner of the group (creator or assigned owner)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_groups'
    )
    
    # Group settings
    is_private = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Workspace details
    workspace_url = models.URLField(blank=True, null=True)
    
    class Meta:
        db_table = 'groups'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
            models.Index(fields=['owner']),
        ]

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        return self.memberships.count()


class GroupMembership(BaseModel):
    """
    Membership relationship between Users and Groups.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='group_memberships'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    role = models.CharField(
        max_length=20,
        choices=GroupRole.choices(),
        default=GroupRole.MEMBER.value
    )
    
    # User preferences for this group
    notifications_enabled = models.BooleanField(default=True)
    is_favorite = models.BooleanField(default=False)
    
    # Display name in this group (optional)
    display_name = models.CharField(max_length=150, blank=True, null=True)
    
    class Meta:
        db_table = 'group_memberships'
        unique_together = ['user', 'group']
        ordering = ['group', 'user']
        indexes = [
            models.Index(fields=['user', 'group']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.user.email} in {self.group.name} ({self.get_role_display()})"
    
    def is_owner(self):
        return self.role == GroupRole.OWNER.value
    
    def is_admin(self):
        return self.role in [GroupRole.OWNER.value, GroupRole.ADMIN.value]
