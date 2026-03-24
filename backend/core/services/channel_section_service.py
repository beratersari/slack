"""
Channel Section service for business logic related to ChannelSection model.
"""
from typing import List, Optional, Dict, Any
from core.models import ChannelSection, ChannelSectionItem, User
from core.repositories import ChannelSectionRepository, ChannelRepository


class ChannelSectionService:
    """
    Service for ChannelSection-related business logic.
    """

    def __init__(self):
        self.section_repository = ChannelSectionRepository()
        self.channel_repository = ChannelRepository()

    def get_user_sections(self, user_id: int, workspace_id: int) -> List[ChannelSection]:
        """Get all sections for a user in a workspace."""
        return self.section_repository.get_user_sections(user_id, workspace_id)

    def get_section_by_id(self, section_id: int) -> Optional[ChannelSection]:
        """Get a section by ID."""
        return self.section_repository.get_by_id(section_id)

    def create_custom_section(self, name: str, user_id: int, workspace_id: int,
                              color: Optional[str] = None, order: int = 0) -> ChannelSection:
        """
        Create a custom section for a user in a workspace.

        Args:
            name: Section name
            user_id: User ID
            workspace_id: Workspace ID
            color: Optional hex color
            order: Section order in sidebar

        Returns:
            Created ChannelSection instance
        """
        # Check if section with same name already exists
        existing = self.section_repository.get_section_by_name(user_id, workspace_id, name)
        if existing:
            raise ValueError(f"Section with name '{name}' already exists")

        return self.section_repository.create(
            name=name,
            user_id=user_id,
            workspace_id=workspace_id,
            section_type='custom',
            color=color,
            order=order
        )

    def update_section(self, section_id: int, user_id: int, **kwargs) -> Optional[ChannelSection]:
        """
        Update a section.

        Only the section owner can update it.
        """
        section = self.section_repository.get_by_id(section_id)
        if not section:
            raise ValueError("Section not found")

        # Check ownership
        if section.user_id != user_id:
            raise ValueError("You can only update your own sections")

        # Don't allow changing section_type
        if 'section_type' in kwargs:
            del kwargs['section_type']

        return self.section_repository.update(section_id, **kwargs)

    def delete_section(self, section_id: int, user_id: int) -> bool:
        """
        Delete a custom section.

        Only the section owner can delete it.
        Default sections cannot be deleted.
        """
        section = self.section_repository.get_by_id(section_id)
        if not section:
            raise ValueError("Section not found")

        if section.user_id != user_id:
            raise ValueError("You can only delete your own sections")

        if section.section_type != 'custom':
            raise ValueError("Default sections cannot be deleted")

        return self.section_repository.delete(section_id)

    def reorder_sections(self, user_id: int, workspace_id: int, section_orders: Dict[int, int]) -> List[ChannelSection]:
        """
        Reorder multiple sections at once.

        Args:
            user_id: User ID
            workspace_id: Workspace ID
            section_orders: Dict mapping section_id to new order
        """
        updated_sections = []
        for section_id, new_order in section_orders.items():
            section = self.section_repository.get_by_id(section_id)
            if section and section.user_id == user_id and section.workspace_id == workspace_id:
                updated = self.section_repository.update_section_order(section_id, new_order)
                if updated:
                    updated_sections.append(updated)
        return updated_sections

    def toggle_section_collapsed(self, section_id: int, user_id: int) -> Optional[ChannelSection]:
        """Toggle the collapsed state of a section."""
        section = self.section_repository.get_by_id(section_id)
        if not section:
            raise ValueError("Section not found")

        if section.user_id != user_id:
            raise ValueError("You can only modify your own sections")

        return self.section_repository.toggle_collapsed(section_id)

    # Channel management within sections

    def add_channel_to_section(self, section_id: int, channel_id: int, user_id: int,
                               order: int = 0) -> ChannelSectionItem:
        """
        Add a channel to a section.

        The user must be a member of both the workspace and the channel.
        """
        section = self.section_repository.get_by_id(section_id)
        if not section:
            raise ValueError("Section not found")

        if section.user_id != user_id:
            raise ValueError("You can only modify your own sections")

        channel = self.channel_repository.get_by_id(channel_id)
        if not channel:
            raise ValueError("Channel not found")

        # Check if channel belongs to the same workspace
        if channel.workspace_id != section.workspace_id:
            raise ValueError("Channel does not belong to this workspace")

        item = self.section_repository.add_channel_to_section(section_id, channel_id, order)
        if not item:
            raise ValueError("Failed to add channel to section")

        return item

    def remove_channel_from_section(self, section_id: int, channel_id: int, user_id: int) -> bool:
        """Remove a channel from a section."""
        section = self.section_repository.get_by_id(section_id)
        if not section:
            raise ValueError("Section not found")

        if section.user_id != user_id:
            raise ValueError("You can only modify your own sections")

        return self.section_repository.remove_channel_from_section(section_id, channel_id)

    def move_channel_to_section(self, channel_id: int, from_section_id: int,
                                to_section_id: int, user_id: int, order: int = 0) -> bool:
        """Move a channel from one section to another."""
        # Verify ownership of both sections
        from_section = self.section_repository.get_by_id(from_section_id)
        to_section = self.section_repository.get_by_id(to_section_id)

        if not from_section or not to_section:
            raise ValueError("Section not found")

        if from_section.user_id != user_id or to_section.user_id != user_id:
            raise ValueError("You can only modify your own sections")

        if from_section.workspace_id != to_section.workspace_id:
            raise ValueError("Sections must be in the same workspace")

        return self.section_repository.move_channel_to_section(
            channel_id, from_section_id, to_section_id, order
        )

    def reorder_channels_in_section(self, section_id: int, user_id: int,
                                    item_orders: Dict[int, int]) -> List[ChannelSectionItem]:
        """
        Reorder channels within a section.

        Args:
            section_id: Section ID
            user_id: User ID
            item_orders: Dict mapping item_id to new order
        """
        section = self.section_repository.get_by_id(section_id)
        if not section:
            raise ValueError("Section not found")

        if section.user_id != user_id:
            raise ValueError("You can only modify your own sections")

        updated_items = []
        for item_id, new_order in item_orders.items():
            updated = self.section_repository.update_channel_order(item_id, new_order)
            if updated:
                updated_items.append(updated)

        return updated_items

    def create_default_sections_for_user(self, user_id: int, workspace_id: int) -> List[ChannelSection]:
        """Create default sections for a user when they join a workspace."""
        return self.section_repository.create_default_sections(user_id, workspace_id)

    def get_section_with_channels(self, section_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Get a section with all its channels."""
        section = self.section_repository.get_by_id(section_id)
        if not section:
            return None

        if section.user_id != user_id:
            raise ValueError("You can only view your own sections")

        items = self.section_repository.get_channel_section_items(section_id)

        return {
            'section': section,
            'items': items
        }
