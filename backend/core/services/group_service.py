"""
Group service for business logic related to Group model.
"""
from typing import List, Optional, Dict, Any
from core.models import Group, GroupMembership, GroupRole, User, UserType
from core.repositories import GroupRepository, UserRepository


class GroupService:
    """
    Service for Group-related business logic.
    """
    
    def __init__(self):
        self.group_repository = GroupRepository()
        self.user_repository = UserRepository()
    
    def get_group_by_id(self, group_id: int) -> Optional[Group]:
        """Get group by ID."""
        return self.group_repository.get_by_id(group_id)
    
    def get_all_groups(self) -> List[Group]:
        """Get all groups."""
        return self.group_repository.get_all()
    
    def get_active_groups(self) -> List[Group]:
        """Get all active groups."""
        return self.group_repository.get_active_groups()
    
    def get_groups_by_owner(self, owner_id: int) -> List[Group]:
        """Get groups owned by a user."""
        return self.group_repository.get_groups_by_owner(owner_id)
    
    def get_groups_by_member(self, user_id: int) -> List[Group]:
        """Get groups where user is a member."""
        return self.group_repository.get_groups_by_member(user_id)
    
    def can_create_group(self, user: User) -> bool:
        """Check if user can create groups."""
        return user.is_admin() or user.is_super_user_type()
    
    def create_group(self, name: str, owner_id: int, description: str = '',
                     is_private: bool = False, **kwargs) -> Group:
        """
        Create a new group.
        
        Only admins and super users can create groups.
        
        Args:
            name: Group name
            owner_id: ID of the group owner
            description: Group description
            is_private: Whether the group is private
            **kwargs: Additional fields
        
        Returns:
            Created Group instance
        
        Raises:
            ValueError: If user cannot create groups or validation fails
        """
        owner = self.user_repository.get_by_id(owner_id)
        if not owner:
            raise ValueError(f"User with ID {owner_id} not found")
        
        if not self.can_create_group(owner):
            raise ValueError("Only admins and super users can create groups")
        
        # Check for duplicate group name
        existing = Group.objects.filter(name=name, is_active=True).first()
        if existing:
            raise ValueError(f"Group with name '{name}' already exists")
        
        return self.group_repository.create_group(
            name=name,
            owner_id=owner_id,
            description=description,
            is_private=is_private,
            **kwargs
        )
    
    def update_group(self, group_id: int, user_id: int, **kwargs) -> Optional[Group]:
        """
        Update group information.
        
        Only group owner or admins can update.
        """
        group = self.group_repository.get_by_id(group_id)
        if not group:
            raise ValueError(f"Group with ID {group_id} not found")
        
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Check permissions
        if not (user.is_admin() or group.owner_id == user_id):
            raise ValueError("Only group owner or admins can update the group")
        
        return self.group_repository.update_group(group_id, **kwargs)
    
    def delete_group(self, group_id: int, user_id: int) -> bool:
        """
        Delete a group (soft delete).
        
        Only group owner or admins can delete.
        """
        group = self.group_repository.get_by_id(group_id)
        if not group:
            raise ValueError(f"Group with ID {group_id} not found")
        
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        if not (user.is_admin() or group.owner_id == user_id):
            raise ValueError("Only group owner or admins can delete the group")
        
        return self.group_repository.archive_group(group_id) is not None
    
    def add_member(self, group_id: int, user_id: int, added_by_id: int,
                   role: str = GroupRole.MEMBER.value) -> GroupMembership:
        """
        Add a member to a group.
        
        Only group admins/owners or system admins/super users can add members.
        """
        group = self.group_repository.get_by_id(group_id)
        if not group:
            raise ValueError(f"Group with ID {group_id} not found")
        
        user_to_add = self.user_repository.get_by_id(user_id)
        if not user_to_add:
            raise ValueError(f"User with ID {user_id} not found")
        
        added_by = self.user_repository.get_by_id(added_by_id)
        if not added_by:
            raise ValueError(f"User with ID {added_by_id} not found")
        
        # Check permissions - admin/super_user can add to any group
        # Group owner/admin can add to their group
        can_add = (
            added_by.is_admin() or 
            added_by.is_super_user_type() or
            self.group_repository.is_admin(group_id, added_by_id)
        )
        
        if not can_add:
            raise ValueError("You don't have permission to add members to this group")
        
        # Check if user is already a member
        if self.group_repository.is_member(group_id, user_id):
            raise ValueError(f"User is already a member of this group")
        
        return self.group_repository.add_member(group_id, user_id, role)
    
    def remove_member(self, group_id: int, user_id: int, removed_by_id: int) -> bool:
        """
        Remove a member from a group.
        
        Only group admins/owners or system admins/super users can remove members.
        """
        group = self.group_repository.get_by_id(group_id)
        if not group:
            raise ValueError(f"Group with ID {group_id} not found")
        
        removed_by = self.user_repository.get_by_id(removed_by_id)
        if not removed_by:
            raise ValueError(f"User with ID {removed_by_id} not found")
        
        # Check permissions
        can_remove = (
            removed_by.is_admin() or 
            removed_by.is_super_user_type() or
            self.group_repository.is_admin(group_id, removed_by_id) or
            user_id == removed_by_id  # Users can remove themselves
        )
        
        if not can_remove:
            raise ValueError("You don't have permission to remove members from this group")
        
        # Cannot remove the group owner
        if group.owner_id == user_id:
            raise ValueError("Cannot remove the group owner. Transfer ownership first.")
        
        return self.group_repository.remove_member(group_id, user_id)
    
    def update_member_role(self, group_id: int, user_id: int, new_role: str,
                           updated_by_id: int) -> GroupMembership:
        """
        Update a member's role in a group.
        
        Only group owner or system admins can update roles.
        """
        group = self.group_repository.get_by_id(group_id)
        if not group:
            raise ValueError(f"Group with ID {group_id} not found")
        
        updated_by = self.user_repository.get_by_id(updated_by_id)
        if not updated_by:
            raise ValueError(f"User with ID {updated_by_id} not found")
        
        # Check permissions
        can_update = (
            updated_by.is_admin() or 
            updated_by.is_super_user_type() or
            group.owner_id == updated_by_id
        )
        
        if not can_update:
            raise ValueError("Only group owner or admins can update member roles")
        
        # Cannot change owner's role
        if group.owner_id == user_id:
            raise ValueError("Cannot change the group owner's role")
        
        return self.group_repository.update_member_role(group_id, user_id, new_role)
    
    def get_group_members(self, group_id: int) -> List[GroupMembership]:
        """Get all members of a group."""
        return self.group_repository.get_group_members(group_id)
    
    def get_member_role(self, group_id: int, user_id: int) -> Optional[str]:
        """Get a user's role in a group."""
        return self.group_repository.get_member_role(group_id, user_id)
    
    def is_member(self, group_id: int, user_id: int) -> bool:
        """Check if user is a member of a group."""
        return self.group_repository.is_member(group_id, user_id)
    
    def search_groups(self, query: str, user_id: Optional[int] = None) -> List[Group]:
        """Search groups by query.
        
        Supports partial matching like Slack - searching for "a" will find
        all groups containing "a" in their name or description.
        """
        if not query:
            return []
        return self.group_repository.search_groups(query, user_id)
    
    def get_group_statistics(self) -> Dict[str, Any]:
        """Get group statistics."""
        return self.group_repository.get_group_statistics()
