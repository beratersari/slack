"""
Repository for Message data access.
"""
from typing import List, Optional, Dict, Any
from django.db.models import Q, Count, Prefetch
from django.utils import timezone
from core.models import Message, MessageEditHistory, Channel, User
from .base_repository import BaseRepository


class MessageRepository(BaseRepository[Message]):
    """
    Repository for Message model data access operations.
    """
    
    def __init__(self):
        super().__init__(Message)
    
    def get_channel_messages(self, channel_id: int, include_deleted: bool = False) -> List[Message]:
        """
        Get all top-level messages for a channel (not replies).
        """
        queryset = Message.objects.filter(
            channel_id=channel_id,
            parent_message__isnull=True  # Only top-level messages
        ).select_related('sender', 'channel')
        
        if not include_deleted:
            queryset = queryset.filter(is_deleted=False)
        
        return list(queryset)
    
    def get_thread_replies(self, message_id: int, include_deleted: bool = False) -> List[Message]:
        """
        Get all replies to a message (thread).
        """
        queryset = Message.objects.filter(
            parent_message_id=message_id
        ).select_related('sender')
        
        if not include_deleted:
            queryset = queryset.filter(is_deleted=False)
        
        return list(queryset)
    
    def get_dm_messages(self, user1_id: int, user2_id: int, include_deleted: bool = False) -> List[Message]:
        """
        Get direct messages between two users.
        """
        queryset = Message.objects.filter(
            Q(sender_id=user1_id, dm_recipient_id=user2_id) |
            Q(sender_id=user2_id, dm_recipient_id=user1_id),
            channel__isnull=True
        ).select_related('sender', 'dm_recipient')
        
        if not include_deleted:
            queryset = queryset.filter(is_deleted=False)
        
        return list(queryset.order_by('created_at'))
    
    def get_user_dm_conversations(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get list of users the current user has DM conversations with.
        Returns list of dicts with user info and last message.
        """
        # Get all DM messages involving the user
        messages = Message.objects.filter(
            Q(sender_id=user_id) | Q(dm_recipient_id=user_id),
            channel__isnull=True,
            is_deleted=False
        ).select_related('sender', 'dm_recipient').order_by('-created_at')
        
        # Track unique conversation partners
        conversations = {}
        for msg in messages:
            partner = msg.dm_recipient if msg.sender_id == user_id else msg.sender
            if partner.id not in conversations:
                conversations[partner.id] = {
                    'user': partner,
                    'last_message': msg,
                    'unread_count': 0  # Could be implemented with read receipts
                }
        
        return list(conversations.values())
    
    def create_message(self, sender_id: int, content: str, 
                       channel_id: Optional[int] = None,
                       dm_recipient_id: Optional[int] = None,
                       parent_message_id: Optional[int] = None) -> Message:
        """
        Create a new message.
        """
        message = Message.objects.create(
            sender_id=sender_id,
            content=content,
            channel_id=channel_id,
            dm_recipient_id=dm_recipient_id,
            parent_message_id=parent_message_id
        )
        return message
    
    def edit_message(self, message_id: int, new_content: str, edited_by_id: int) -> Optional[Message]:
        """
        Edit a message and save the old content to history.
        """
        try:
            message = Message.objects.get(pk=message_id, is_deleted=False)
            
            # Save old content to history
            MessageEditHistory.objects.create(
                message_id=message_id,
                old_content=message.content,
                edited_by_id=edited_by_id
            )
            
            # Update message
            message.content = new_content
            message.is_edited = True
            message.edited_at = timezone.now()
            message.save(update_fields=['content', 'is_edited', 'edited_at', 'updated_at'])
            
            return message
        except Message.DoesNotExist:
            return None
    
    def soft_delete_message(self, message_id: int, deleted_by_id: int) -> Optional[Message]:
        """
        Soft delete a message (mark as deleted).
        """
        try:
            message = Message.objects.get(pk=message_id, is_deleted=False)
            message.is_deleted = True
            message.deleted_at = timezone.now()
            message.deleted_by_id = deleted_by_id
            message.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by', 'updated_at'])
            return message
        except Message.DoesNotExist:
            return None
    
    def get_edit_history(self, message_id: int) -> List[MessageEditHistory]:
        """
        Get edit history for a message.
        """
        return list(MessageEditHistory.objects.filter(
            message_id=message_id
        ).select_related('edited_by'))
    
    def get_message_by_id(self, message_id: int, include_deleted: bool = False) -> Optional[Message]:
        """
        Get a message by ID.
        """
        try:
            queryset = Message.objects.filter(pk=message_id)
            if not include_deleted:
                queryset = queryset.filter(is_deleted=False)
            return queryset.select_related('sender', 'channel', 'dm_recipient', 'parent_message').first()
        except Message.DoesNotExist:
            return None
    
    def get_messages_count_by_channel(self, channel_id: int) -> int:
        """
        Get count of messages in a channel.
        """
        return Message.objects.filter(channel_id=channel_id, is_deleted=False).count()
    
    def get_thread_count(self, message_id: int) -> int:
        """
        Get count of replies in a thread.
        """
        return Message.objects.filter(parent_message_id=message_id, is_deleted=False).count()
    
    def search_messages(self, query: str, user_id: int, 
                        channel_id: Optional[int] = None) -> List[Message]:
        """
        Search messages by content.
        """
        from core.models import Channel, ChannelMembership
        
        queryset = Message.objects.filter(
            content__icontains=query,
            is_deleted=False
        ).select_related('sender', 'channel')
        
        if channel_id:
            queryset = queryset.filter(channel_id=channel_id)
        
        # Filter to only show messages in channels the user has access to
        user_channel_ids = ChannelMembership.objects.filter(
            user_id=user_id
        ).values_list('channel_id', flat=True)
        
        queryset = queryset.filter(
            Q(channel_id__in=user_channel_ids) | Q(dm_recipient_id=user_id) | Q(sender_id=user_id)
        )
        
        return list(queryset.order_by('-created_at')[:50])  # Limit to 50 results
