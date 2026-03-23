"""
Group repository for database operations related to Group model.
"""
from typing import List, Optional, Dict, Any
from django.db.models import Q, Count
from core.models import Group, GroupMembership, GroupRole
from .base_repository import BaseRepository


class GroupRepository(BaseRepository[Group]):
    """
    Repository for Group model with specific group-related operations.
    """
    
    def __init__(self):
        super().__init__(Group)
    
    def get_active_groups(self) -> List[Group]:
        """Get all active groups."""
        return list(Group.objects.filter(is_active=True))
    
    def get_groups_by_owner(self, owner_id: int) -> List[Group]:
        """Get all groups owned by a user."""
        return list(Group.objects.filter(owner_id=owner_id, is_active=True))
    
    def get_groups_by_member(self, user_id: int) -> List[Group]:
        """Get all groups where user is a member."""
        return list(Group.objects.filter(
            memberships__user_id=user_id,
            is_active=True
        ).distinct())
    
    def get_public_groups(self) -> List[Group]:
        """Get all public groups."""
        return list(Group.objects.filter(is_private=False, is_active=True))
    
    def get_private_groups(self) -> List[Group]:
        """Get all private groups."""
        return list(Group.objects.filter(is_private=True, is_active=True))
    
    def get_group_with_members(self, group_id: int) -> Optional[Group]:
        """Get group with prefetched members."""
        try:
            return Group.objects.prefetch_related('memberships__user').get(id=group_id)
        except Group.DoesNotExist:
            return None
    
    def create_group(self, name: str, owner_id: int, **kwargs) -> Group:
        """Create a new group."""
        from core.models import User
        owner = User.objects.get(id=owner_id)
        group = Group.objects.create(name=name, owner=owner, **kwargs)
        
        # Add owner as a member with OWNER role
        GroupMembership.objects.create(
            user=owner,
            group=group,
            role=GroupRole.OWNER.value
        )
        
        return group
    
    def update_group(self, group_id: int, **kwargs) -> Optional[Group]:
        """Update group information."""
        group = self.get_by_id(group_id)
        if group:
            for key, value in kwargs.items():
                setattr(group, key, value)
            group.save()
            return group
        return None
    
    def archive_group(self, group_id: int) -> Optional[Group]:
        """Archive a group (soft delete)."""
        return self.update_group(group_id, is_active=False)
    
    def add_member(self, group_id: int, user_id: int, role: str = GroupRole.MEMBER.value) -> Optional[GroupMembership]:
        """Add a member to a group."""
        from core.models import User
        
        group = self.get_by_id(group_id)
        user = User.objects.filter(id=user_id).first()
        
        if group and user:
            membership, created = GroupMembership.objects.get_or_create(
                user=user,
                group=group,
                defaults={'role': role}
            )
            if not created:
                # Update role if membership already exists
                membership.role = role
                membership.save()
            return membership
        return None
    
    def remove_member(self, group_id: int, user_id: int) -> bool:
        """Remove a member from a group."""
        deleted, _ = GroupMembership.objects.filter(
            group_id=group_id,
            user_id=user_id
        ).delete()
        return deleted > 0
    
    def update_member_role(self, group_id: int, user_id: int, role: str) -> Optional[GroupMembership]:
        """Update a member's role in a group."""
        try:
            membership = GroupMembership.objects.get(
                group_id=group_id,
                user_id=user_id
            )
            membership.role = role
            membership.save()
            return membership
        except GroupMembership.DoesNotExist:
            return None
    
    def get_group_members(self, group_id: int) -> List[GroupMembership]:
        """Get all members of a group."""
        return list(GroupMembership.objects.filter(group_id=group_id).select_related('user'))
    
    def get_member_role(self, group_id: int, user_id: int) -> Optional[str]:
        """Get a user's role in a group."""
        try:
            membership = GroupMembership.objects.get(
                group_id=group_id,
                user_id=user_id
            )
            return membership.role
        except GroupMembership.DoesNotExist:
            return None
    
    def is_member(self, group_id: int, user_id: int) -> bool:
        """Check if user is a member of a group."""
        return GroupMembership.objects.filter(
            group_id=group_id,
            user_id=user_id
        ).exists()
    
    def is_admin(self, group_id: int, user_id: int) -> bool:
        """Check if user is an admin or owner of a group."""
        return GroupMembership.objects.filter(
            group_id=group_id,
            user_id=user_id,
            role__in=[GroupRole.OWNER.value, GroupRole.ADMIN.value]
        ).exists()
    
    def search_groups(self, query: str, user_id: Optional[int] = None) -> List[Group]:
        """Search groups by name or description."""
        queryset = Group.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            is_active=True
        )
        
        if user_id:
            # Return only groups the user can see
            queryset = queryset.filter(
                Q(is_private=False) | Q(memberships__user_id=user_id)
            ).distinct()
        
        return list(queryset)
    
    def get_group_statistics(self) -> Dict[str, Any]:
        """Get group statistics."""
        return {
            'total_groups': Group.objects.count(),
            'active_groups': Group.objects.filter(is_active=True).count(),
            'private_groups': Group.objects.filter(is_private=True, is_active=True).count(),
            'public_groups': Group.objects.filter(is_private=False, is_active=True).count(),
        }
