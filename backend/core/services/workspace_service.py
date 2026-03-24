"""
Workspace service for business logic related to Workspace model.
"""
from typing import List, Optional, Dict, Any
from core.models import Workspace, WorkspaceMembership, WorkspaceRole, User, UserType
from core.repositories import WorkspaceRepository, UserRepository


class WorkspaceService:
    """
    Service for Workspace-related business logic.
    """

    def __init__(self):
        self.workspace_repository = WorkspaceRepository()
        self.user_repository = UserRepository()

    def get_workspace_by_id(self, workspace_id: int) -> Optional[Workspace]:
        """Get workspace by ID."""
        return self.workspace_repository.get_by_id(workspace_id)

    def get_all_workspaces(self) -> List[Workspace]:
        """Get all workspaces."""
        return self.workspace_repository.get_all()

    def get_active_workspaces(self) -> List[Workspace]:
        """Get all active workspaces."""
        return self.workspace_repository.get_active_workspaces()

    def get_workspaces_by_owner(self, owner_id: int) -> List[Workspace]:
        """Get workspaces owned by a user."""
        return self.workspace_repository.get_workspaces_by_owner(owner_id)

    def get_workspaces_by_member(self, user_id: int) -> List[Workspace]:
        """Get workspaces where user is a member."""
        return self.workspace_repository.get_workspaces_by_member(user_id)

    def can_create_workspace(self, user: User) -> bool:
        """Check if user can create workspaces."""
        return user.is_admin() or user.is_super_user_type()

    def create_workspace(self, name: str, owner_id: int, description: str = '',
                         is_private: bool = False, **kwargs) -> Workspace:
        """
        Create a new workspace.

        Only admins and super users can create workspaces.

        Args:
            name: Workspace name
            owner_id: ID of the workspace owner
            description: Workspace description
            is_private: Whether the workspace is private
            **kwargs: Additional fields

        Returns:
            Created Workspace instance

        Raises:
            ValueError: If user cannot create workspaces or validation fails
        """
        owner = self.user_repository.get_by_id(owner_id)
        if not owner:
            raise ValueError(f"User with ID {owner_id} not found")

        if not self.can_create_workspace(owner):
            raise ValueError("Only admins and super users can create workspaces")

        # Check for duplicate workspace name
        existing = Workspace.objects.filter(name=name, is_active=True).first()
        if existing:
            raise ValueError(f"Workspace with name '{name}' already exists")

        return self.workspace_repository.create_workspace(
            name=name,
            owner_id=owner_id,
            description=description,
            is_private=is_private,
            **kwargs
        )

    def update_workspace(self, workspace_id: int, user_id: int, **kwargs) -> Optional[Workspace]:
        """
        Update workspace information.

        Only workspace owner or admins can update.
        """
        workspace = self.workspace_repository.get_by_id(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace with ID {workspace_id} not found")

        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        # Check permissions
        if not (user.is_admin() or workspace.owner_id == user_id):
            raise ValueError("Only workspace owner or admins can update the workspace")

        return self.workspace_repository.update_workspace(workspace_id, **kwargs)

    def delete_workspace(self, workspace_id: int, user_id: int) -> bool:
        """
        Delete a workspace (soft delete).

        Only workspace owner or admins can delete.
        """
        workspace = self.workspace_repository.get_by_id(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace with ID {workspace_id} not found")

        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        if not (user.is_admin() or workspace.owner_id == user_id):
            raise ValueError("Only workspace owner or admins can delete the workspace")

        return self.workspace_repository.archive_workspace(workspace_id) is not None

    def add_member(self, workspace_id: int, user_id: int, added_by_id: int,
                   role: str = WorkspaceRole.MEMBER.value) -> WorkspaceMembership:
        """
        Add a member to a workspace.

        Only workspace admins/owners or system admins/super users can add members.
        """
        workspace = self.workspace_repository.get_by_id(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace with ID {workspace_id} not found")

        user_to_add = self.user_repository.get_by_id(user_id)
        if not user_to_add:
            raise ValueError(f"User with ID {user_id} not found")

        added_by = self.user_repository.get_by_id(added_by_id)
        if not added_by:
            raise ValueError(f"User with ID {added_by_id} not found")

        # Check permissions - admin/super_user can add to any workspace
        # Workspace owner/admin can add to their workspace
        can_add = (
            added_by.is_admin() or
            added_by.is_super_user_type() or
            self.workspace_repository.is_admin(workspace_id, added_by_id)
        )

        if not can_add:
            raise ValueError("You don't have permission to add members to this workspace")

        # Check if user is already a member
        if self.workspace_repository.is_member(workspace_id, user_id):
            raise ValueError(f"User is already a member of this workspace")

        return self.workspace_repository.add_member(workspace_id, user_id, role)

    def remove_member(self, workspace_id: int, user_id: int, removed_by_id: int) -> bool:
        """
        Remove a member from a workspace.

        Only workspace admins/owners or system admins/super users can remove members.
        """
        workspace = self.workspace_repository.get_by_id(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace with ID {workspace_id} not found")

        removed_by = self.user_repository.get_by_id(removed_by_id)
        if not removed_by:
            raise ValueError(f"User with ID {removed_by_id} not found")

        # Check permissions
        can_remove = (
            removed_by.is_admin() or
            removed_by.is_super_user_type() or
            self.workspace_repository.is_admin(workspace_id, removed_by_id) or
            user_id == removed_by_id  # Users can remove themselves
        )

        if not can_remove:
            raise ValueError("You don't have permission to remove members from this workspace")

        # Cannot remove the workspace owner
        if workspace.owner_id == user_id:
            raise ValueError("Cannot remove the workspace owner. Transfer ownership first.")

        return self.workspace_repository.remove_member(workspace_id, user_id)

    def update_member_role(self, workspace_id: int, user_id: int, new_role: str,
                           updated_by_id: int) -> WorkspaceMembership:
        """
        Update a member's role in a workspace.

        Only workspace owner or system admins can update roles.
        """
        workspace = self.workspace_repository.get_by_id(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace with ID {workspace_id} not found")

        updated_by = self.user_repository.get_by_id(updated_by_id)
        if not updated_by:
            raise ValueError(f"User with ID {updated_by_id} not found")

        # Check permissions
        can_update = (
            updated_by.is_admin() or
            updated_by.is_super_user_type() or
            workspace.owner_id == updated_by_id
        )

        if not can_update:
            raise ValueError("Only workspace owner or admins can update member roles")

        # Cannot change owner's role
        if workspace.owner_id == user_id:
            raise ValueError("Cannot change the workspace owner's role")

        return self.workspace_repository.update_member_role(workspace_id, user_id, new_role)

    def get_workspace_members(self, workspace_id: int) -> List[WorkspaceMembership]:
        """Get all members of a workspace."""
        return self.workspace_repository.get_workspace_members(workspace_id)

    def get_member_role(self, workspace_id: int, user_id: int) -> Optional[str]:
        """Get a user's role in a workspace."""
        return self.workspace_repository.get_member_role(workspace_id, user_id)

    def is_member(self, workspace_id: int, user_id: int) -> bool:
        """Check if user is a member of a workspace."""
        return self.workspace_repository.is_member(workspace_id, user_id)

    def search_workspaces(self, query: str, user_id: Optional[int] = None) -> List[Workspace]:
        """Search workspaces by query.

        Supports partial matching like Slack - searching for "a" will find
        all workspaces containing "a" in their name or description.
        """
        if not query:
            return []
        return self.workspace_repository.search_workspaces(query, user_id)

    def get_workspace_statistics(self) -> Dict[str, Any]:
        """Get workspace statistics."""
        return self.workspace_repository.get_workspace_statistics()
