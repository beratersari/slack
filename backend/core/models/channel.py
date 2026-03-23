"""
Channel model for communication channels within groups.
"""
from enum import Enum
from django.db import models
from django.conf import settings
from .base import BaseModel
from .group import Group


class ChannelType(Enum):
    """
    Enum for channel types.
    """
    PUBLIC = 'public'
    PRIVATE = 'private'
    DIRECT = 'direct'

    @classmethod
    def choices(cls):
        return [(tag.value, tag.name.title()) for tag in cls]


class ChannelRole(Enum):
    """
    Enum for channel member roles.
    """
    OWNER = 'owner'
    MEMBER = 'member'
    GUEST = 'guest'

    @classmethod
    def choices(cls):
        return [(tag.value, tag.name.title()) for tag in cls]


class Channel(BaseModel):
    """
    Channel model for communication within groups.
    
    Channels are where conversations happen. Each channel belongs to a group.
    """
    name = models.CharField(max_length=80, db_index=True)
    description = models.TextField(blank=True, null=True)
    topic = models.CharField(max_length=250, blank=True, null=True)
    
    # Group this channel belongs to
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='channels'
    )
    
    # Creator of the channel
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_channels'
    )
    
    # Channel type
    channel_type = models.CharField(
        max_length=20,
        choices=ChannelType.choices(),
        default=ChannelType.PUBLIC.value
    )
    
    # Channel settings
    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)
    
    # For direct messages, store the other user
    dm_with = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='dm_channels'
    )
    
    class Meta:
        db_table = 'channels'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['group']),
            models.Index(fields=['channel_type']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"#{self.name} ({self.group.name})"

    @property
    def member_count(self):
        return self.memberships.count()

    def is_public(self):
        return self.channel_type == ChannelType.PUBLIC.value

    def is_private(self):
        return self.channel_type == ChannelType.PRIVATE.value

    def is_direct(self):
        return self.channel_type == ChannelType.DIRECT.value


class ChannelMembership(BaseModel):
    """
    Membership relationship between Users and Channels.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='channel_memberships'
    )
    channel = models.ForeignKey(
        Channel,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    role = models.CharField(
        max_length=20,
        choices=ChannelRole.choices(),
        default=ChannelRole.MEMBER.value
    )
    
    # User preferences for this channel
    notifications_enabled = models.BooleanField(default=True)
    is_favorite = models.BooleanField(default=False)
    is_muted = models.BooleanField(default=False)
    
    # Last read timestamp for unread count
    last_read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'channel_memberships'
        unique_together = ['user', 'channel']
        ordering = ['channel', 'user']
        indexes = [
            models.Index(fields=['user', 'channel']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.user.email} in #{self.channel.name} ({self.get_role_display()})"
    
    def is_owner(self):
        return self.role == ChannelRole.OWNER.value
