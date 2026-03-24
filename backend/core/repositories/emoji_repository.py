"""
Emoji repository for database operations related to MessageReaction and CustomEmoji models.
"""
from typing import List, Optional, Dict
from django.db.models import Count, Q
from core.models import MessageReaction, CustomEmoji, Message, Workspace
from .base_repository import BaseRepository


class MessageReactionRepository(BaseRepository[MessageReaction]):
    """
    Repository for MessageReaction model with reaction-specific operations.
    """

    def __init__(self):
        super().__init__(MessageReaction)

    def get_message_reactions(self, message_id: int) -> List[MessageReaction]:
        """Get all reactions for a message."""
        return list(MessageReaction.objects.filter(
            message_id=message_id
        ).select_related('user', 'custom_emoji'))

    def get_reaction_summary(self, message_id: int) -> Dict[str, dict]:
        """
        Get a summary of reactions for a message.
        Returns: {emoji: {'count': int, 'users': [user_ids], 'has_custom': bool}}
        """
        reactions = self.get_message_reactions(message_id)
        summary = {}

        for reaction in reactions:
            emoji_key = reaction.emoji
            if emoji_key not in summary:
                summary[emoji_key] = {
                    'count': 0,
                    'users': [],
                    'has_custom': reaction.custom_emoji is not None,
                    'custom_emoji_id': reaction.custom_emoji_id
                }
            summary[emoji_key]['count'] += 1
            summary[emoji_key]['users'].append(reaction.user_id)

        return summary

    def get_user_reaction(self, message_id: int, user_id: int, emoji: str) -> Optional[MessageReaction]:
        """Check if a user has already reacted with this emoji."""
        try:
            return MessageReaction.objects.get(
                message_id=message_id,
                user_id=user_id,
                emoji=emoji
            )
        except MessageReaction.DoesNotExist:
            return None

    def add_reaction(self, message_id: int, user_id: int, emoji: str,
                     custom_emoji_id: Optional[int] = None) -> MessageReaction:
        """Add a reaction to a message."""
        return self.create(
            message_id=message_id,
            user_id=user_id,
            emoji=emoji,
            custom_emoji_id=custom_emoji_id
        )

    def remove_reaction(self, message_id: int, user_id: int, emoji: str) -> bool:
        """Remove a user's reaction from a message."""
        deleted, _ = MessageReaction.objects.filter(
            message_id=message_id,
            user_id=user_id,
            emoji=emoji
        ).delete()
        return deleted > 0

    def remove_all_user_reactions(self, message_id: int, user_id: int) -> int:
        """Remove all reactions from a user on a message."""
        deleted, _ = MessageReaction.objects.filter(
            message_id=message_id,
            user_id=user_id
        ).delete()
        return deleted

    def has_user_reacted(self, message_id: int, user_id: int, emoji: str) -> bool:
        """Check if a user has reacted with a specific emoji."""
        return MessageReaction.objects.filter(
            message_id=message_id,
            user_id=user_id,
            emoji=emoji
        ).exists()


class CustomEmojiRepository(BaseRepository[CustomEmoji]):
    """
    Repository for CustomEmoji model with emoji-specific operations.
    """

    def __init__(self):
        super().__init__(CustomEmoji)

    def get_workspace_emojis(self, workspace_id: int) -> List[CustomEmoji]:
        """Get all custom emojis for a workspace."""
        return list(CustomEmoji.objects.filter(
            workspace_id=workspace_id
        ).select_related('alias_for').order_by('name'))

    def get_emoji_by_name(self, workspace_id: int, name: str) -> Optional[CustomEmoji]:
        """Get a custom emoji by workspace and name."""
        try:
            return CustomEmoji.objects.get(
                workspace_id=workspace_id,
                name=name.lower()
            )
        except CustomEmoji.DoesNotExist:
            return None

    def search_emojis(self, workspace_id: int, query: str) -> List[CustomEmoji]:
        """Search custom emojis by name."""
        return list(CustomEmoji.objects.filter(
            workspace_id=workspace_id,
            name__icontains=query.lower()
        ).order_by('name'))

    def create_emoji(self, name: str, image, workspace_id: int, created_by_id: int) -> CustomEmoji:
        """Create a new custom emoji."""
        return self.create(
            name=name.lower(),
            image=image,
            workspace_id=workspace_id,
            created_by_id=created_by_id
        )

    def create_alias(self, name: str, alias_for_id: int, workspace_id: int,
                     created_by_id: int) -> CustomEmoji:
        """Create an alias (shortcut) for an existing emoji."""
        return self.create(
            name=name.lower(),
            alias_for_id=alias_for_id,
            workspace_id=workspace_id,
            created_by_id=created_by_id,
            image=''  # Aliases don't have their own image
        )

    def get_popular_emojis(self, workspace_id: int, limit: int = 10) -> List[CustomEmoji]:
        """Get most frequently used custom emojis."""
        return list(CustomEmoji.objects.filter(
            workspace_id=workspace_id
        ).order_by('-usage_count')[:limit])

    def can_user_create_emoji(self, workspace_id: int, user_id: int) -> bool:
        """
        Check if user can create emoji in workspace.
        Typically workspace admins or members with permission.
        """
        from core.models import WorkspaceMembership, WorkspaceRole

        try:
            membership = WorkspaceMembership.objects.get(
                workspace_id=workspace_id,
                user_id=user_id
            )
            # Admin and Owner can create emojis
            return membership.role in [WorkspaceRole.ADMIN.value, WorkspaceRole.OWNER.value]
        except WorkspaceMembership.DoesNotExist:
            return False

    def delete_emoji(self, emoji_id: int, user_id: int) -> bool:
        """Delete a custom emoji (only creator or admin can delete)."""
        try:
            emoji = CustomEmoji.objects.get(id=emoji_id)

            # Check if user is creator or workspace admin
            if emoji.created_by_id == user_id:
                return self.delete(emoji_id)

            # Check if user is workspace admin
            from core.models import WorkspaceMembership, WorkspaceRole
            try:
                membership = WorkspaceMembership.objects.get(
                    workspace_id=emoji.workspace_id,
                    user_id=user_id
                )
                if membership.role in [WorkspaceRole.ADMIN.value, WorkspaceRole.OWNER.value]:
                    return self.delete(emoji_id)
            except WorkspaceMembership.DoesNotExist:
                pass

            return False
        except CustomEmoji.DoesNotExist:
            return False
