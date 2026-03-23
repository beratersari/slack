"""
Message model for channel messages and direct messages.
Supports threading (replies), edit history, and soft deletion.
"""
from django.db import models
from django.conf import settings
from .base import BaseModel


class Message(BaseModel):
    """
    Message model for channel messages and DMs.
    
    Features:
    - Channel messages: sent to a channel
    - Direct messages: sent directly to another user
    - Threading: reply to a message creates a thread
    - Edit history: all edits are preserved
    - Soft delete: messages are marked as deleted, not removed
    """
    
    # Content
    content = models.TextField()
    
    # Sender
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='messages_sent'
    )
    
    # Destination - either channel OR direct message recipient
    channel = models.ForeignKey(
        'Channel',
        on_delete=models.CASCADE,
        related_name='messages',
        null=True,
        blank=True
    )
    dm_recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='messages_received',
        null=True,
        blank=True,
        help_text='For direct messages, the recipient user'
    )
    
    # Threading - reply to another message
    parent_message = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='replies',
        null=True,
        blank=True,
        help_text='If this is a reply, the parent message'
    )
    
    # Edit tracking
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages_deleted'
    )
    
    class Meta:
        db_table = 'messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['channel', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
            models.Index(fields=['parent_message']),
            models.Index(fields=['dm_recipient']),
        ]
    
    def __str__(self):
        preview = self.content[:50] + '...' if len(self.content) > 50 else self.content
        return f"Message from {self.sender.email}: {preview}"
    
    @property
    def is_thread_parent(self):
        """Check if this message has replies (is a thread parent)."""
        return self.replies.exists()
    
    @property
    def is_reply(self):
        """Check if this message is a reply to another message."""
        return self.parent_message is not None
    
    @property
    def reply_count(self):
        """Get the count of direct replies."""
        return self.replies.filter(is_deleted=False).count()
    
    @property
    def is_dm(self):
        """Check if this is a direct message."""
        return self.dm_recipient is not None
    
    def can_edit(self, user):
        """Check if a user can edit this message."""
        if self.is_deleted:
            return False
        # Owner can edit their own message
        if self.sender_id == user.id:
            return True
        # Admin can edit any message
        if user.user_type == 'admin':
            return True
        return False
    
    def can_delete(self, user):
        """Check if a user can delete this message."""
        if self.is_deleted:
            return False
        # Owner can delete their own message
        if self.sender_id == user.id:
            return True
        # Admin can delete any message
        if user.user_type == 'admin':
            return True
        return False


class MessageEditHistory(BaseModel):
    """
    History of message edits.
    
    Every time a message is edited, the previous content is saved here.
    This allows viewing the full edit history of any message.
    """
    
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='edit_history'
    )
    
    old_content = models.TextField(
        help_text='The content before this edit'
    )
    
    edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='message_edits'
    )
    
    edited_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'message_edit_history'
        ordering = ['-edited_at']
        verbose_name_plural = 'Message edit histories'
    
    def __str__(self):
        preview = self.old_content[:30] + '...' if len(self.old_content) > 30 else self.old_content
        return f"Edit of message {self.message_id}: {preview}"
