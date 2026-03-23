"""
Channel repository for database operations related to Channel model.
"""
from typing import List, Optional, Dict, Any
from django.db.models import Q, Count
from core.models import Channel, ChannelMembership, ChannelRole, ChannelType
from .base_repository import BaseRepository


class ChannelRepository(BaseRepository[Channel]):
    """
    Repository for Channel model with specific channel-related operations.
    """
    
    def __init__(self):
        super().__init__(Channel)
    
    def get_active_channels(self) -> List[Channel]:
        """Get all active channels."""
        return list(Channel.objects.filter(is_active=True))
    
    def get_channels_by_group(self, group_id: int) -> List[Channel]:
        """Get all channels in a group."""
        return list(Channel.objects.filter(group_id=group_id, is_active=True))
    
    def get_channels_by_creator(self, user_id: int) -> List[Channel]:
        """Get all channels created by a user."""
        return list(Channel.objects.filter(created_by_id=user_id, is_active=True))
    
    def get_channels_by_member(self, user_id: int) -> List[Channel]:
        """Get all channels where user is a member."""
        return list(Channel.objects.filter(
            memberships__user_id=user_id,
            is_active=True
        ).distinct())
    
    def get_public_channels(self, group_id: int) -> List[Channel]:
        """Get all public channels in a group."""
        return list(Channel.objects.filter(
            group_id=group_id,
            channel_type=ChannelType.PUBLIC.value,
            is_active=True
        ))
    
    def get_private_channels(self, group_id: int) -> List[Channel]:
        """Get all private channels in a group."""
        return list(Channel.objects.filter(
            group_id=group_id,
            channel_type=ChannelType.PRIVATE.value,
            is_active=True
        ))
    
    def get_channel_with_members(self, channel_id: int) -> Optional[Channel]:
        """Get channel with prefetched members."""
        try:
            return Channel.objects.prefetch_related('memberships__user').get(id=channel_id)
        except Channel.DoesNotExist:
            return None
    
    def create_channel(self, name: str, group_id: int, created_by_id: int, 
                       channel_type: str = ChannelType.PUBLIC.value, **kwargs) -> Channel:
        """Create a new channel."""
        from core.models import Group, User
        
        group = Group.objects.get(id=group_id)
        creator = User.objects.get(id=created_by_id)
        
        channel = Channel.objects.create(
            name=name,
            group=group,
            created_by=creator,
            channel_type=channel_type,
            **kwargs
        )
        
        # Add creator as a member with OWNER role
        ChannelMembership.objects.create(
            user=creator,
            channel=channel,
            role=ChannelRole.OWNER.value
        )
        
        return channel
    
    def update_channel(self, channel_id: int, **kwargs) -> Optional[Channel]:
        """Update channel information."""
        channel = self.get_by_id(channel_id)
        if channel:
            for key, value in kwargs.items():
                setattr(channel, key, value)
            channel.save()
            return channel
        return None
    
    def archive_channel(self, channel_id: int) -> Optional[Channel]:
        """Archive a channel."""
        return self.update_channel(channel_id, is_archived=True)
    
    def delete_channel(self, channel_id: int) -> bool:
        """Soft delete a channel."""
        return self.update_channel(channel_id, is_active=False) is not None
    
    def add_member(self, channel_id: int, user_id: int, role: str = ChannelRole.MEMBER.value) -> Optional[ChannelMembership]:
        """Add a member to a channel."""
        from core.models import User
        
        channel = self.get_by_id(channel_id)
        user = User.objects.filter(id=user_id).first()
        
        if channel and user:
            membership, created = ChannelMembership.objects.get_or_create(
                user=user,
                channel=channel,
                defaults={'role': role}
            )
            if not created:
                membership.role = role
                membership.save()
            return membership
        return None
    
    def remove_member(self, channel_id: int, user_id: int) -> bool:
        """Remove a member from a channel."""
        deleted, _ = ChannelMembership.objects.filter(
            channel_id=channel_id,
            user_id=user_id
        ).delete()
        return deleted > 0
    
    def update_member_role(self, channel_id: int, user_id: int, role: str) -> Optional[ChannelMembership]:
        """Update a member's role in a channel."""
        try:
            membership = ChannelMembership.objects.get(
                channel_id=channel_id,
                user_id=user_id
            )
            membership.role = role
            membership.save()
            return membership
        except ChannelMembership.DoesNotExist:
            return None
    
    def get_channel_members(self, channel_id: int) -> List[ChannelMembership]:
        """Get all members of a channel."""
        return list(ChannelMembership.objects.filter(channel_id=channel_id).select_related('user'))
    
    def get_member_role(self, channel_id: int, user_id: int) -> Optional[str]:
        """Get a user's role in a channel."""
        try:
            membership = ChannelMembership.objects.get(
                channel_id=channel_id,
                user_id=user_id
            )
            return membership.role
        except ChannelMembership.DoesNotExist:
            return None
    
    def is_member(self, channel_id: int, user_id: int) -> bool:
        """Check if user is a member of a channel."""
        return ChannelMembership.objects.filter(
            channel_id=channel_id,
            user_id=user_id
        ).exists()
    
    def is_owner(self, channel_id: int, user_id: int) -> bool:
        """Check if user is owner of a channel."""
        return ChannelMembership.objects.filter(
            channel_id=channel_id,
            user_id=user_id,
            role=ChannelRole.OWNER.value
        ).exists()
    
    def search_channels(self, query: str, group_id: Optional[int] = None, 
                        user_id: Optional[int] = None) -> List[Channel]:
        """Search channels by name or description."""
        queryset = Channel.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query) | Q(topic__icontains=query),
            is_active=True
        )
        
        if group_id:
            queryset = queryset.filter(group_id=group_id)
        
        if user_id:
            # Return only channels the user can see
            queryset = queryset.filter(
                Q(channel_type=ChannelType.PUBLIC.value) | Q(memberships__user_id=user_id)
            ).distinct()
        
        return list(queryset)
    
    def get_or_create_dm_channel(self, user1_id: int, user2_id: int, group_id: int) -> Channel:
        """Get or create a direct message channel between two users."""
        from core.models import User, Group
        
        # Try to find existing DM channel
        existing = Channel.objects.filter(
            group_id=group_id,
            channel_type=ChannelType.DIRECT.value,
            memberships__user_id=user1_id
        ).filter(
            memberships__user_id=user2_id
        ).first()
        
        if existing:
            return existing
        
        # Create new DM channel
        user1 = User.objects.get(id=user1_id)
        user2 = User.objects.get(id=user2_id)
        group = Group.objects.get(id=group_id)
        
        channel_name = f"dm-{min(user1_id, user2_id)}-{max(user1_id, user2_id)}"
        
        channel = Channel.objects.create(
            name=channel_name,
            group=group,
            created_by=user1,
            channel_type=ChannelType.DIRECT.value,
            dm_with=user2
        )
        
        # Add both users as members
        ChannelMembership.objects.create(user=user1, channel=channel, role=ChannelRole.OWNER.value)
        ChannelMembership.objects.create(user=user2, channel=channel, role=ChannelRole.MEMBER.value)
        
        return channel
    
    def get_channel_statistics(self, group_id: Optional[int] = None) -> Dict[str, Any]:
        """Get channel statistics."""
        base_query = Channel.objects.filter(is_active=True)
        
        if group_id:
            base_query = base_query.filter(group_id=group_id)
        
        return {
            'total_channels': base_query.count(),
            'public_channels': base_query.filter(channel_type=ChannelType.PUBLIC.value).count(),
            'private_channels': base_query.filter(channel_type=ChannelType.PRIVATE.value).count(),
            'direct_channels': base_query.filter(channel_type=ChannelType.DIRECT.value).count(),
            'archived_channels': Channel.objects.filter(is_archived=True).count(),
        }
