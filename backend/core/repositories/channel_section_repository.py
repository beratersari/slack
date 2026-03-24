"""
Channel Section repository for database operations related to ChannelSection model.
"""
from typing import List, Optional
from django.db.models import Q
from core.models import ChannelSection, ChannelSectionItem, Channel, Workspace
from .base_repository import BaseRepository


class ChannelSectionRepository(BaseRepository[ChannelSection]):
    """
    Repository for ChannelSection model with specific section-related operations.
    """

    def __init__(self):
        super().__init__(ChannelSection)

    def get_user_sections(self, user_id: int, workspace_id: int) -> List[ChannelSection]:
        """Get all sections for a user in a workspace."""
        return list(ChannelSection.objects.filter(
            user_id=user_id,
            workspace_id=workspace_id
        ).prefetch_related('items__channel'))

    def get_default_sections(self, user_id: int, workspace_id: int) -> List[ChannelSection]:
        """Get default sections for a user (starred, channels, direct_messages)."""
        return list(ChannelSection.objects.filter(
            user_id=user_id,
            workspace_id=workspace_id,
            section_type__in=['starred', 'channels', 'direct_messages']
        ))

    def get_custom_sections(self, user_id: int, workspace_id: int) -> List[ChannelSection]:
        """Get custom sections created by the user."""
        return list(ChannelSection.objects.filter(
            user_id=user_id,
            workspace_id=workspace_id,
            section_type='custom'
        ))

    def get_section_by_name(self, user_id: int, workspace_id: int, name: str) -> Optional[ChannelSection]:
        """Get a section by name for a user in a workspace."""
        try:
            return ChannelSection.objects.get(
                user_id=user_id,
                workspace_id=workspace_id,
                name=name
            )
        except ChannelSection.DoesNotExist:
            return None

    def create_default_sections(self, user_id: int, workspace_id: int) -> List[ChannelSection]:
        """Create default sections for a new user in a workspace."""
        defaults = [
            {'name': 'Starred', 'section_type': 'starred', 'order': 0},
            {'name': 'Channels', 'section_type': 'channels', 'order': 1},
            {'name': 'Direct Messages', 'section_type': 'direct_messages', 'order': 2},
        ]

        sections = []
        for default in defaults:
            section, created = ChannelSection.objects.get_or_create(
                user_id=user_id,
                workspace_id=workspace_id,
                section_type=default['section_type'],
                defaults={
                    'name': default['name'],
                    'order': default['order']
                }
            )
            sections.append(section)

        return sections

    def update_section_order(self, section_id: int, new_order: int) -> Optional[ChannelSection]:
        """Update the order of a section."""
        section = self.get_by_id(section_id)
        if section:
            section.order = new_order
            section.save()
            return section
        return None

    def toggle_collapsed(self, section_id: int) -> Optional[ChannelSection]:
        """Toggle the collapsed state of a section."""
        section = self.get_by_id(section_id)
        if section:
            section.is_collapsed = not section.is_collapsed
            section.save()
            return section
        return None

    # Channel Section Item operations

    def add_channel_to_section(self, section_id: int, channel_id: int, order: int = 0) -> Optional[ChannelSectionItem]:
        """Add a channel to a section."""
        from core.models import Channel

        section = self.get_by_id(section_id)
        channel = Channel.objects.filter(id=channel_id).first()

        if section and channel:
            item, created = ChannelSectionItem.objects.get_or_create(
                section=section,
                channel=channel,
                defaults={'order': order}
            )
            if not created:
                item.order = order
                item.save()
            return item
        return None

    def remove_channel_from_section(self, section_id: int, channel_id: int) -> bool:
        """Remove a channel from a section."""
        deleted, _ = ChannelSectionItem.objects.filter(
            section_id=section_id,
            channel_id=channel_id
        ).delete()
        return deleted > 0

    def update_channel_order(self, item_id: int, new_order: int) -> Optional[ChannelSectionItem]:
        """Update the order of a channel within a section."""
        try:
            item = ChannelSectionItem.objects.get(id=item_id)
            item.order = new_order
            item.save()
            return item
        except ChannelSectionItem.DoesNotExist:
            return None

    def get_channel_section_items(self, section_id: int) -> List[ChannelSectionItem]:
        """Get all channel items in a section."""
        return list(ChannelSectionItem.objects.filter(
            section_id=section_id
        ).select_related('channel').order_by('order'))

    def move_channel_to_section(self, channel_id: int, from_section_id: int, to_section_id: int, order: int = 0) -> bool:
        """Move a channel from one section to another."""
        try:
            item = ChannelSectionItem.objects.get(
                channel_id=channel_id,
                section_id=from_section_id
            )
            item.section_id = to_section_id
            item.order = order
            item.save()
            return True
        except ChannelSectionItem.DoesNotExist:
            return False
