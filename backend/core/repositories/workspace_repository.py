"""
Workspace repository for database operations related to Workspace model.
"""
from typing import List, Optional, Dict, Any
from django.db.models import Q, Count
from core.models import Workspace, WorkspaceMembership, WorkspaceRole
from .base_repository import BaseRepository


class WorkspaceRepository(BaseRepository[Workspace]):
    """
    Repository for Workspace model with specific workspace-related operations.
    """

    def __init__(self):
        super().__init__(Workspace)

    def get_active_workspaces(self) -> List[Workspace]:
        """Get all active workspaces."""
        return list(Workspace.objects.filter(is_active=True))

    def get_workspaces_by_owner(self, owner_id: int) -> List[Workspace]:
        """Get all workspaces owned by a user."""
        return list(Workspace.objects.filter(owner_id=owner_id, is_active=True))

    def get_workspaces_by_member(self, user_id: int) -> List[Workspace]:
        """Get all workspaces where user is a member."""
        return list(Workspace.objects.filter(
            memberships__user_id=user_id,
            is_active=True
        ).distinct())

    def get_public_workspaces(self) -> List[Workspace]:
        """Get all public workspaces."""
        return list(Workspace.objects.filter(is_private=False, is_active=True))

    def get_private_workspaces(self) -> List[Workspace]:
        """Get all private workspaces."""
        return list(Workspace.objects.filter(is_private=True, is_active=True))

    def get_workspace_with_members(self, workspace_id: int) -> Optional[Workspace]:
        """Get workspace with prefetched members."""
        try:
            return Workspace.objects.prefetch_related('memberships__user').get(id=workspace_id)
        except Workspace.DoesNotExist:
            return None

    def create_workspace(self, name: str, owner_id: int, **kwargs) -> Workspace:
        """Create a new workspace."""
        from core.models import User
        owner = User.objects.get(id=owner_id)
        workspace = Workspace.objects.create(name=name, owner=owner, **kwargs)

        # Add owner as a member with OWNER role
        WorkspaceMembership.objects.create(
            user=owner,
            workspace=workspace,
            role=WorkspaceRole.OWNER.value
        )

        return workspace

    def update_workspace(self, workspace_id: int, **kwargs) -> Optional[Workspace]:
        """Update workspace information."""
        workspace = self.get_by_id(workspace_id)
        if workspace:
            for key, value in kwargs.items():
                setattr(workspace, key, value)
            workspace.save()
            return workspace
        return None

    def archive_workspace(self, workspace_id: int) -> Optional[Workspace]:
        """Archive a workspace (soft delete)."""
        return self.update_workspace(workspace_id, is_active=False)

    def add_member(self, workspace_id: int, user_id: int, role: str = WorkspaceRole.MEMBER.value) -> Optional[WorkspaceMembership]:
        """Add a member to a workspace."""
        from core.models import User

        workspace = self.get_by_id(workspace_id)
        user = User.objects.filter(id=user_id).first()

        if workspace and user:
            membership, created = WorkspaceMembership.objects.get_or_create(
                user=user,
                workspace=workspace,
                defaults={'role': role}
            )
            if not created:
                # Update role if membership already exists
                membership.role = role
                membership.save()
            return membership
        return None

    def remove_member(self, workspace_id: int, user_id: int) -> bool:
        """Remove a member from a workspace."""
        deleted, _ = WorkspaceMembership.objects.filter(
            workspace_id=workspace_id,
            user_id=user_id
        ).delete()
        return deleted > 0

    def update_member_role(self, workspace_id: int, user_id: int, role: str) -> Optional[WorkspaceMembership]:
        """Update a member's role in a workspace."""
        try:
            membership = WorkspaceMembership.objects.get(
                workspace_id=workspace_id,
                user_id=user_id
            )
            membership.role = role
            membership.save()
            return membership
        except WorkspaceMembership.DoesNotExist:
            return None

    def get_workspace_members(self, workspace_id: int) -> List[WorkspaceMembership]:
        """Get all members of a workspace."""
        return list(WorkspaceMembership.objects.filter(workspace_id=workspace_id).select_related('user'))

    def get_member_role(self, workspace_id: int, user_id: int) -> Optional[str]:
        """Get a user's role in a workspace."""
        try:
            membership = WorkspaceMembership.objects.get(
                workspace_id=workspace_id,
                user_id=user_id
            )
            return membership.role
        except WorkspaceMembership.DoesNotExist:
            return None

    def is_member(self, workspace_id: int, user_id: int) -> bool:
        """Check if user is a member of a workspace."""
        return WorkspaceMembership.objects.filter(
            workspace_id=workspace_id,
            user_id=user_id
        ).exists()

    def is_admin(self, workspace_id: int, user_id: int) -> bool:
        """Check if user is an admin or owner of a workspace."""
        return WorkspaceMembership.objects.filter(
            workspace_id=workspace_id,
            user_id=user_id,
            role__in=[WorkspaceRole.OWNER.value, WorkspaceRole.ADMIN.value]
        ).exists()

    def search_workspaces(self, query: str, user_id: Optional[int] = None) -> List[Workspace]:
        """Search workspaces by name or description."""
        queryset = Workspace.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            is_active=True
        )

        if user_id:
            # Return only workspaces the user can see
            queryset = queryset.filter(
                Q(is_private=False) | Q(memberships__user_id=user_id)
            ).distinct()

        return list(queryset)

    def get_workspace_statistics(self) -> Dict[str, Any]:
        """Get workspace statistics."""
        return {
            'total_workspaces': Workspace.objects.count(),
            'active_workspaces': Workspace.objects.filter(is_active=True).count(),
            'private_workspaces': Workspace.objects.filter(is_private=True, is_active=True).count(),
            'public_workspaces': Workspace.objects.filter(is_private=False, is_active=True).count(),
        }
