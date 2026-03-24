"""
Emoji service for business logic related to MessageReaction and CustomEmoji models.
"""
from typing import List, Optional, Dict, Any
from core.models import MessageReaction, CustomEmoji, Message, Workspace, User
from core.repositories import MessageReactionRepository, CustomEmojiRepository


class EmojiService:
    """
    Service for emoji-related business logic.
    Handles message reactions and custom emojis.
    """

    def __init__(self):
        self.reaction_repository = MessageReactionRepository()
        self.emoji_repository = CustomEmojiRepository()

    # ============================================
    # Message Reactions
    # ============================================

    def get_message_reactions(self, message_id: int) -> Dict[str, Any]:
        """
        Get all reactions for a message with summary.

        Returns:
            {
                'reactions': [
                    {
                        'emoji': '👍',
                        'count': 3,
                        'users': [1, 2, 3],
                        'has_custom': False
                    },
                    ...
                ],
                'total_count': 5
            }
        """
        summary = self.reaction_repository.get_reaction_summary(message_id)
        reactions_list = []
        total_count = 0

        for emoji, data in summary.items():
            reactions_list.append({
                'emoji': emoji,
                'count': data['count'],
                'users': data['users'],
                'has_custom': data['has_custom'],
                'custom_emoji_id': data.get('custom_emoji_id')
            })
            total_count += data['count']

        return {
            'reactions': reactions_list,
            'total_count': total_count
        }

    def add_reaction(self, message_id: int, user_id: int, emoji: str) -> MessageReaction:
        """
        Add a reaction to a message.

        Args:
            message_id: Message ID
            user_id: User ID
            emoji: Unicode emoji (👍) or custom emoji shortcode (:party-parrot:)

        Returns:
            Created MessageReaction
        """
        from core.repositories import MessageRepository

        # Verify message exists
        message_repo = MessageRepository()
        message = message_repo.get_by_id(message_id)
        if not message:
            raise ValueError("Message not found")

        # Check if already reacted
        existing = self.reaction_repository.get_user_reaction(message_id, user_id, emoji)
        if existing:
            raise ValueError("You have already reacted with this emoji")

        # Check if it's a custom emoji
        custom_emoji_id = None
        if emoji.startswith(':') and emoji.endswith(':'):
            # Extract name from :emoji-name:
            emoji_name = emoji[1:-1]

            # Get the message's workspace to find custom emoji
            workspace_id = message.channel.workspace_id if message.channel else None
            if workspace_id:
                custom_emoji = self.emoji_repository.get_emoji_by_name(workspace_id, emoji_name)
                if custom_emoji:
                    custom_emoji_id = custom_emoji.id
                    custom_emoji.increment_usage()
                else:
                    raise ValueError(f"Custom emoji {emoji} not found")

        return self.reaction_repository.add_reaction(
            message_id=message_id,
            user_id=user_id,
            emoji=emoji,
            custom_emoji_id=custom_emoji_id
        )

    def remove_reaction(self, message_id: int, user_id: int, emoji: str) -> bool:
        """
        Remove a user's reaction from a message.

        Returns:
            True if removed, False if reaction didn't exist
        """
        return self.reaction_repository.remove_reaction(message_id, user_id, emoji)

    def toggle_reaction(self, message_id: int, user_id: int, emoji: str) -> Dict[str, Any]:
        """
        Toggle a reaction on/off.

        Returns:
            {'action': 'added'|'removed', 'reaction': reaction|null}
        """
        existing = self.reaction_repository.get_user_reaction(message_id, user_id, emoji)

        if existing:
            # Remove existing reaction
            self.reaction_repository.remove_reaction(message_id, user_id, emoji)
            return {'action': 'removed', 'reaction': None}
        else:
            # Add new reaction
            reaction = self.add_reaction(message_id, user_id, emoji)
            return {'action': 'added', 'reaction': reaction}

    def get_user_reactions(self, user_id: int, limit: int = 50) -> List[MessageReaction]:
        """Get recent reactions by a user."""
        return list(MessageReaction.objects.filter(
            user_id=user_id
        ).select_related('message').order_by('-created_at')[:limit])

    # ============================================
    # Custom Emojis
    # ============================================

    def get_workspace_emojis(self, workspace_id: int) -> List[CustomEmoji]:
        """Get all custom emojis for a workspace."""
        return self.emoji_repository.get_workspace_emojis(workspace_id)

    def get_emoji_by_name(self, workspace_id: int, name: str) -> Optional[CustomEmoji]:
        """Get a custom emoji by name."""
        return self.emoji_repository.get_emoji_by_name(workspace_id, name)

    def create_custom_emoji(self, name: str, image, workspace_id: int,
                           created_by_id: int) -> CustomEmoji:
        """
        Create a new custom emoji.

        Args:
            name: Emoji shortcode without colons (e.g., 'party-parrot')
            image: Image file (PNG, GIF, JPG)
            workspace_id: Workspace ID
            created_by_id: User ID creating the emoji

        Returns:
            Created CustomEmoji
        """
        # Validate name (letters, numbers, hyphens, underscores only)
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            raise ValueError("Emoji name can only contain letters, numbers, hyphens, and underscores")

        # Check if emoji already exists
        existing = self.emoji_repository.get_emoji_by_name(workspace_id, name)
        if existing:
            raise ValueError(f"Emoji :{name}: already exists in this workspace")

        # Check permissions
        if not self.emoji_repository.can_user_create_emoji(workspace_id, created_by_id):
            raise ValueError("You don't have permission to create emojis in this workspace")

        return self.emoji_repository.create_emoji(
            name=name.lower(),
            image=image,
            workspace_id=workspace_id,
            created_by_id=created_by_id
        )

    def create_emoji_alias(self, alias_name: str, original_emoji_id: int,
                          workspace_id: int, created_by_id: int) -> CustomEmoji:
        """
        Create an alias (alternative name) for an existing emoji.

        Args:
            alias_name: New shortcode for the emoji
            original_emoji_id: ID of the emoji to alias
            workspace_id: Workspace ID
            created_by_id: User ID

        Returns:
            Created alias CustomEmoji
        """
        # Get original emoji
        original = self.emoji_repository.get_by_id(original_emoji_id)
        if not original:
            raise ValueError("Original emoji not found")

        if original.workspace_id != workspace_id:
            raise ValueError("Cannot create alias for emoji in different workspace")

        # Check if alias name already exists
        existing = self.emoji_repository.get_emoji_by_name(workspace_id, alias_name)
        if existing:
            raise ValueError(f"Emoji :{alias_name}: already exists")

        # Check permissions
        if not self.emoji_repository.can_user_create_emoji(workspace_id, created_by_id):
            raise ValueError("You don't have permission to create emoji aliases")

        return self.emoji_repository.create_alias(
            name=alias_name.lower(),
            alias_for_id=original_emoji_id,
            workspace_id=workspace_id,
            created_by_id=created_by_id
        )

    def delete_custom_emoji(self, emoji_id: int, user_id: int) -> bool:
        """
        Delete a custom emoji.

        Returns:
            True if deleted, False if not allowed or not found
        """
        result = self.emoji_repository.delete_emoji(emoji_id, user_id)
        if not result:
            raise ValueError("Emoji not found or you don't have permission to delete it")
        return result

    def search_emojis(self, workspace_id: int, query: str) -> List[CustomEmoji]:
        """Search custom emojis by name."""
        return self.emoji_repository.search_emojis(workspace_id, query)

    def get_popular_emojis(self, workspace_id: int, limit: int = 10) -> List[CustomEmoji]:
        """Get most frequently used custom emojis."""
        return self.emoji_repository.get_popular_emojis(workspace_id, limit)

    def get_emoji_stats(self, emoji_id: int) -> Dict[str, Any]:
        """
        Get usage statistics for a custom emoji.

        Returns:
            {
                'emoji': CustomEmoji,
                'reaction_count': int,
                'usage_count': int
            }
        """
        emoji = self.emoji_repository.get_by_id(emoji_id)
        if not emoji:
            raise ValueError("Emoji not found")

        reaction_count = MessageReaction.objects.filter(
            custom_emoji_id=emoji_id
        ).count()

        return {
            'emoji': emoji,
            'reaction_count': reaction_count,
            'usage_count': emoji.usage_count
        }
