"""
Channel Section model for organizing channels in the sidebar.
Each user can create custom sections to organize their channels.
"""
from django.db import models
from django.conf import settings
from .base import BaseModel


class ChannelSection(BaseModel):
    """
    Custom section for organizing channels in the sidebar.
    Each user has their own sections per workspace.
    """
    name = models.CharField(max_length=100)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='channel_sections'
    )
    workspace = models.ForeignKey(
        'Workspace',
        on_delete=models.CASCADE,
        related_name='channel_sections'
    )

    # For ordering sections in the sidebar (lower = higher)
    order = models.PositiveIntegerField(default=0)

    # Visual customization
    color = models.CharField(max_length=20, blank=True, null=True)  # Hex color

    # Section type: 'custom', 'starred', 'channels', 'direct_messages'
    section_type = models.CharField(max_length=20, default='custom')

    # Whether section is collapsed in the UI
    is_collapsed = models.BooleanField(default=False)

    class Meta:
        db_table = 'channel_sections'
        ordering = ['order', 'name']
        unique_together = ['user', 'workspace', 'name']
        indexes = [
            models.Index(fields=['user', 'workspace']),
            models.Index(fields=['order']),
            models.Index(fields=['section_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.user.email})"

    @property
    def channel_count(self):
        return self.items.count()


class ChannelSectionItem(BaseModel):
    """
    Maps a channel to a user's custom section.
    This allows users to organize channels within their sections.
    """
    section = models.ForeignKey(
        ChannelSection,
        on_delete=models.CASCADE,
        related_name='items'
    )
    channel = models.ForeignKey(
        'Channel',
        on_delete=models.CASCADE,
        related_name='section_items'
    )

    # For ordering channels within the section (lower = higher)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'channel_section_items'
        ordering = ['order']
        unique_together = ['section', 'channel']
        indexes = [
            models.Index(fields=['section', 'order']),
        ]

    def __str__(self):
        return f"{self.channel.name} in {self.section.name}"
