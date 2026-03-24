"""
Workspace model for workspace/organization management.
"""
from enum import Enum
from django.db import models
from django.conf import settings
from .base import BaseModel


class WorkspaceRole(Enum):
    """
    Enum for workspace member roles.
    """
    OWNER = 'owner'
    ADMIN = 'admin'
    MEMBER = 'member'
    GUEST = 'guest'

    @classmethod
    def choices(cls):
        return [(tag.value, tag.name.title()) for tag in cls]


class Workspace(BaseModel):
    """
    Workspace model representing a workspace/organization.

    Workspaces are the top-level organizational unit in the Slack clone.
    Users can be members of multiple workspaces.
    """
    name = models.CharField(max_length=100, db_index=True)
    description = models.TextField(blank=True, null=True)
    icon = models.URLField(blank=True, null=True)

    # Owner of the workspace (creator or assigned owner)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_workspaces'
    )

    # Workspace settings
    is_private = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # Workspace details
    workspace_url = models.URLField(blank=True, null=True)

    class Meta:
        db_table = 'workspaces'
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


class WorkspaceMembership(BaseModel):
    """
    Membership relationship between Users and Workspaces.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='workspace_memberships'
    )
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    role = models.CharField(
        max_length=20,
        choices=WorkspaceRole.choices(),
        default=WorkspaceRole.MEMBER.value
    )

    # User preferences for this workspace
    notifications_enabled = models.BooleanField(default=True)
    is_favorite = models.BooleanField(default=False)

    # Display name in this workspace (optional)
    display_name = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        db_table = 'workspace_memberships'
        unique_together = ['user', 'workspace']
        ordering = ['workspace', 'user']
        indexes = [
            models.Index(fields=['user', 'workspace']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.user.email} in {self.workspace.name} ({self.get_role_display()})"

    def is_owner(self):
        return self.role == WorkspaceRole.OWNER.value

    def is_admin(self):
        return self.role in [WorkspaceRole.OWNER.value, WorkspaceRole.ADMIN.value]
