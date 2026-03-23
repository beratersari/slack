"""
Channel service for business logic related to Channel model.
"""
from typing import List, Optional, Dict, Any
from core.models import Channel, ChannelMembership, ChannelRole, ChannelType, User, UserType
from core.repositories import ChannelRepository, GroupRepository, UserRepository


class ChannelService:
    """
    Service for Channel-related business logic.
    """
    
    def __init__(self):
        self.channel_repository = ChannelRepository()
        self.group_repository = GroupRepository()
        self.user_repository = UserRepository()
    
    def get_channel_by_id(self, channel_id: int) -> Optional[Channel]:
        """Get channel by ID."""
        return self.channel_repository.get_by_id(channel_id)
    
    def get_all_channels(self) -> List[Channel]:
        """Get all channels."""
        return self.channel_repository.get_all()
    
    def get_active_channels(self) -> List[Channel]:
        """Get all active channels."""
        return self.channel_repository.get_active_channels()
    
    def get_channels_by_group(self, group_id: int) -> List[Channel]:
        """Get all channels in a group."""
        return self.channel_repository.get_channels_by_group(group_id)
    
    def get_channels_by_member(self, user_id: int) -> List[Channel]:
        """Get all channels where user is a member."""
        return self.channel_repository.get_channels_by_member(user_id)
    
    def can_create_channel(self, user: User, group_id: int) -> bool:
        """Check if user can create channels in a group."""
        # Admins and super users can create channels anywhere
        if user.is_admin() or user.is_super_user_type():
            return True
        
        # Group admins/owners can create channels in their group
        return self.group_repository.is_admin(group_id, user.id)
    
    def create_channel(self, name: str, group_id: int, created_by_id: int,
                       channel_type: str = ChannelType.PUBLIC.value,
                       description: str = '', topic: str = '', **kwargs) -> Channel:
        """
        Create a new channel.
        
        Only admins, super users, and group admins can create channels.
        
        Args:
            name: Channel name
            group_id: ID of the group
            created_by_id: ID of the channel creator
            channel_type: Type of channel (public, private, direct)
            description: Channel description
            topic: Channel topic
            **kwargs: Additional fields
        
        Returns:
            Created Channel instance
        
        Raises:
            ValueError: If user cannot create channels or validation fails
        """
        creator = self.user_repository.get_by_id(created_by_id)
        if not creator:
            raise ValueError(f"User with ID {created_by_id} not found")
        
        group = self.group_repository.get_by_id(group_id)
        if not group:
            raise ValueError(f"Group with ID {group_id} not found")
        
        if not self.can_create_channel(creator, group_id):
            raise ValueError("You don't have permission to create channels in this group")
        
        # Check for duplicate channel name in the group
        existing = Channel.objects.filter(
            name=name, 
            group_id=group_id, 
            is_active=True
        ).first()
        if existing:
            raise ValueError(f"Channel with name '{name}' already exists in this group")
        
        return self.channel_repository.create_channel(
            name=name,
            group_id=group_id,
            created_by_id=created_by_id,
            channel_type=channel_type,
            description=description,
            topic=topic,
            **kwargs
        )
    
    def update_channel(self, channel_id: int, user_id: int, **kwargs) -> Optional[Channel]:
        """
        Update channel information.
        
        Only channel owner, group owner, or admins can update.
        """
        channel = self.channel_repository.get_by_id(channel_id)
        if not channel:
            raise ValueError(f"Channel with ID {channel_id} not found")
        
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Check permissions
        can_update = (
            user.is_admin() or 
            user.is_super_user_type() or
            channel.created_by_id == user_id or
            channel.group.owner_id == user_id
        )
        
        if not can_update:
            raise ValueError("You don't have permission to update this channel")
        
        return self.channel_repository.update_channel(channel_id, **kwargs)
    
    def delete_channel(self, channel_id: int, user_id: int) -> bool:
        """
        Delete a channel (soft delete).
        
        Only channel owner, group owner, or admins can delete.
        """
        channel = self.channel_repository.get_by_id(channel_id)
        if not channel:
            raise ValueError(f"Channel with ID {channel_id} not found")
        
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Check permissions
        can_delete = (
            user.is_admin() or 
            user.is_super_user_type() or
            channel.created_by_id == user_id or
            channel.group.owner_id == user_id
        )
        
        if not can_delete:
            raise ValueError("You don't have permission to delete this channel")
        
        return self.channel_repository.delete_channel(channel_id)
    
    def archive_channel(self, channel_id: int, user_id: int) -> Optional[Channel]:
        """Archive a channel."""
        return self.update_channel(channel_id, user_id, is_archived=True)
    
    def add_member(self, channel_id: int, user_id: int, added_by_id: int,
                   role: str = ChannelRole.MEMBER.value) -> ChannelMembership:
        """
        Add a member to a channel.
        
        Only channel owner, group admins, or system admins can add members.
        """
        channel = self.channel_repository.get_by_id(channel_id)
        if not channel:
            raise ValueError(f"Channel with ID {channel_id} not found")
        
        user_to_add = self.user_repository.get_by_id(user_id)
        if not user_to_add:
            raise ValueError(f"User with ID {user_id} not found")
        
        added_by = self.user_repository.get_by_id(added_by_id)
        if not added_by:
            raise ValueError(f"User with ID {added_by_id} not found")
        
        # Check if user is a member of the group first
        if not self.group_repository.is_member(channel.group_id, user_id):
            raise ValueError("User must be a member of the group first")
        
        # Check permissions
        can_add = (
            added_by.is_admin() or 
            added_by.is_super_user_type() or
            self.channel_repository.is_owner(channel_id, added_by_id) or
            self.group_repository.is_admin(channel.group_id, added_by_id)
        )
        
        if not can_add:
            raise ValueError("You don't have permission to add members to this channel")
        
        # Check if user is already a member
        if self.channel_repository.is_member(channel_id, user_id):
            raise ValueError(f"User is already a member of this channel")
        
        return self.channel_repository.add_member(channel_id, user_id, role)
    
    def remove_member(self, channel_id: int, user_id: int, removed_by_id: int) -> bool:
        """
        Remove a member from a channel.
        
        Only channel owner, group admins, or system admins can remove members.
        Users can also remove themselves.
        """
        channel = self.channel_repository.get_by_id(channel_id)
        if not channel:
            raise ValueError(f"Channel with ID {channel_id} not found")
        
        removed_by = self.user_repository.get_by_id(removed_by_id)
        if not removed_by:
            raise ValueError(f"User with ID {removed_by_id} not found")
        
        # Check permissions
        can_remove = (
            removed_by.is_admin() or 
            removed_by.is_super_user_type() or
            self.channel_repository.is_owner(channel_id, removed_by_id) or
            self.group_repository.is_admin(channel.group_id, removed_by_id) or
            user_id == removed_by_id  # Users can remove themselves
        )
        
        if not can_remove:
            raise ValueError("You don't have permission to remove members from this channel")
        
        return self.channel_repository.remove_member(channel_id, user_id)
    
    def get_channel_members(self, channel_id: int) -> List[ChannelMembership]:
        """Get all members of a channel."""
        return self.channel_repository.get_channel_members(channel_id)
    
    def get_member_role(self, channel_id: int, user_id: int) -> Optional[str]:
        """Get a user's role in a channel."""
        return self.channel_repository.get_member_role(channel_id, user_id)
    
    def is_member(self, channel_id: int, user_id: int) -> bool:
        """Check if user is a member of a channel."""
        return self.channel_repository.is_member(channel_id, user_id)
    
    def search_channels(self, query: str, group_id: Optional[int] = None,
                        user_id: Optional[int] = None) -> List[Channel]:
        """Search channels by query.
        
        Supports partial matching like Slack - searching for "a" will find
        all channels containing "a" in their name, description, or topic.
        """
        if not query:
            return []
        return self.channel_repository.search_channels(query, group_id, user_id)
    
    def get_or_create_dm_channel(self, user1_id: int, user2_id: int, 
                                  group_id: int) -> Channel:
        """
        Get or create a direct message channel between two users.
        """
        # Both users must be members of the group
        if not self.group_repository.is_member(group_id, user1_id):
            raise ValueError("User 1 is not a member of the group")
        if not self.group_repository.is_member(group_id, user2_id):
            raise ValueError("User 2 is not a member of the group")
        
        return self.channel_repository.get_or_create_dm_channel(
            user1_id, user2_id, group_id
        )
    
    def get_channel_statistics(self, group_id: Optional[int] = None) -> Dict[str, Any]:
        """Get channel statistics."""
        return self.channel_repository.get_channel_statistics(group_id)
    
    def join_public_channel(self, channel_id: int, user_id: int) -> ChannelMembership:
        """
        Join a public channel.
        
        User must be a member of the group.
        """
        channel = self.channel_repository.get_by_id(channel_id)
        if not channel:
            raise ValueError(f"Channel with ID {channel_id} not found")
        
        if not channel.is_public():
            raise ValueError("Can only join public channels without invitation")
        
        # Check if user is a member of the group
        if not self.group_repository.is_member(channel.group_id, user_id):
            raise ValueError("You must be a member of the group to join channels")
        
        # Check if already a member
        if self.channel_repository.is_member(channel_id, user_id):
            raise ValueError("You are already a member of this channel")
        
        return self.channel_repository.add_member(channel_id, user_id)
