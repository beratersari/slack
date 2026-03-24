"""
Emoji models for reactions and custom emojis.
"""
from django.db import models
from django.conf import settings
from .base import BaseModel


class MessageReaction(BaseModel):
    """
    Emoji reactions on messages (like Slack's 👍, ❤️, 😂 reactions).
    Each user can react once per emoji per message.
    """
    message = models.ForeignKey(
        'Message',
        on_delete=models.CASCADE,
        related_name='reactions'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='message_reactions'
    )

    # The emoji - can be Unicode emoji (👍) or custom emoji shortcode (:party-parrot:)
    emoji = models.CharField(max_length=50)

    # For custom emojis, store reference to the custom emoji
    custom_emoji = models.ForeignKey(
        'CustomEmoji',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reactions'
    )

    class Meta:
        db_table = 'message_reactions'
        ordering = ['created_at']
        unique_together = ['message', 'user', 'emoji']
        indexes = [
            models.Index(fields=['message', 'emoji']),
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} reacted {self.emoji} to message {self.message.id}"

    @property
    def is_custom_emoji(self):
        return self.custom_emoji is not None


class CustomEmoji(BaseModel):
    """
    Custom emojis uploaded by workspace admins/users.
    Like Slack's :party-parrot:, :company-logo:, etc.
    """
    name = models.CharField(
        max_length=50,
        help_text="Emoji shortcode without colons, e.g., 'party-parrot'"
    )

    # The actual image file
    image = models.FileField(
        upload_to='custom_emojis/%Y/%m/',
        help_text="Emoji image file (PNG, GIF, JPG)"
    )

    # Which workspace this emoji belongs to
    workspace = models.ForeignKey(
        'Workspace',
        on_delete=models.CASCADE,
        related_name='custom_emojis'
    )

    # Who created this emoji
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_emojis'
    )

    # Optional alias/shortcut for another emoji
    alias_for = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='aliases'
    )

    # Usage statistics
    usage_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'custom_emojis'
        ordering = ['name']
        unique_together = ['workspace', 'name']
        indexes = [
            models.Index(fields=['workspace', 'name']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        return f":{self.name}: ({self.workspace.name})"

    @property
    def shortcode(self):
        return f":{self.name}:"

    @property
    def is_alias(self):
        return self.alias_for is not None

    def increment_usage(self):
        """Increment usage counter when emoji is used."""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])
