"""
Service for Message business logic.
"""
from typing import List, Optional, Dict, Any
from core.models import Message, MessageEditHistory, Channel, ChannelMembership, User
from core.repositories.message_repository import MessageRepository
from core.repositories.channel_repository import ChannelRepository
from core.services.base_service import BaseService


class MessageService(BaseService):
    """
    Service for Message business logic.
    
    Handles:
    - Sending messages to channels
    - Sending direct messages
    - Creating thread replies
    - Editing messages with history tracking
    - Soft deleting messages
    - Permission checks (owner vs admin)
    """
    
    def __init__(self):
        super().__init__()
        self.repository = MessageRepository()
        self.channel_repository = ChannelRepository()
    
    def send_channel_message(self, sender: User, channel_id: int, content: str) -> Message:
        """
        Send a message to a channel.
        
        Raises:
            ValueError: If channel doesn't exist or user isn't a member
        """
        # Check if channel exists
        channel = self.channel_repository.get_by_id(channel_id)
        if not channel:
            raise ValueError('Channel not found')
        
        # Check if user is a member of the channel
        if not self.channel_repository.is_member(channel_id, sender.id):
            raise ValueError('You are not a member of this channel')
        
        return self.repository.create_message(
            sender_id=sender.id,
            content=content,
            channel_id=channel_id
        )
    
    def send_direct_message(self, sender: User, recipient_id: int, content: str) -> Message:
        """
        Send a direct message to another user.
        
        Raises:
            ValueError: If recipient doesn't exist
        """
        from core.repositories.user_repository import UserRepository
        user_repo = UserRepository()
        
        recipient = user_repo.get_by_id(recipient_id)
        if not recipient:
            raise ValueError('Recipient not found')
        
        if recipient.id == sender.id:
            raise ValueError('Cannot send DM to yourself')
        
        return self.repository.create_message(
            sender_id=sender.id,
            content=content,
            dm_recipient_id=recipient_id
        )
    
    def _has_channel_access(self, user: User, channel_id: int) -> bool:
        """
        Check if user has access to a channel.
        Admins and super users have access to all channels.
        """
        if user.is_admin() or user.is_super_user_type():
            return True
        return self.channel_repository.is_member(channel_id, user.id)

    def reply_to_message(self, sender: User, parent_message_id: int, content: str) -> Message:
        """
        Reply to a message (create a thread).
        
        Raises:
            ValueError: If parent message doesn't exist or user doesn't have access
        """
        parent = self.repository.get_message_by_id(parent_message_id)
        if not parent:
            raise ValueError('Parent message not found')
        
        # Check access: user must be in the same channel or be part of the DM
        if parent.channel:
            if not self._has_channel_access(sender, parent.channel_id):
                raise ValueError('You do not have access to this channel')
            return self.repository.create_message(
                sender_id=sender.id,
                content=content,
                channel_id=parent.channel_id,
                parent_message_id=parent_message_id
            )
        elif parent.is_dm:
            # For DMs, only the sender or recipient can reply
            if sender.id not in [parent.sender_id, parent.dm_recipient_id]:
                raise ValueError('You do not have access to this conversation')
            # Reply goes back to the original sender of parent
            dm_recipient = parent.sender if parent.dm_recipient_id == sender.id else parent.dm_recipient
            return self.repository.create_message(
                sender_id=sender.id,
                content=content,
                dm_recipient_id=dm_recipient.id,
                parent_message_id=parent_message_id
            )
        else:
            raise ValueError('Cannot reply to this message')
    
    def get_channel_messages(self, channel_id: int, user: User) -> List[Message]:
        """
        Get all messages in a channel.
        
        Raises:
            ValueError: If user doesn't have access to the channel
        """
        if not self._has_channel_access(user, channel_id):
            raise ValueError('You do not have access to this channel')
        
        return self.repository.get_channel_messages(channel_id)
    
    def get_thread_replies(self, message_id: int, user: User) -> List[Message]:
        """
        Get all replies in a thread.
        
        Raises:
            ValueError: If user doesn't have access
        """
        parent = self.repository.get_message_by_id(message_id)
        if not parent:
            raise ValueError('Message not found')
        
        # Check access
        if parent.channel:
            if not self._has_channel_access(user, parent.channel_id):
                raise ValueError('You do not have access to this channel')
        elif parent.is_dm:
            if user.id not in [parent.sender_id, parent.dm_recipient_id]:
                raise ValueError('You do not have access to this conversation')
        
        return self.repository.get_thread_replies(message_id)
    
    def get_dm_conversation(self, user: User, other_user_id: int) -> List[Message]:
        """
        Get DM conversation between two users.
        
        Raises:
            ValueError: If other user doesn't exist
        """
        from core.repositories.user_repository import UserRepository
        user_repo = UserRepository()
        
        other_user = user_repo.get_by_id(other_user_id)
        if not other_user:
            raise ValueError('User not found')
        
        return self.repository.get_dm_messages(user.id, other_user_id)
    
    def get_dm_conversations_list(self, user: User) -> List[Dict[str, Any]]:
        """
        Get list of all DM conversations for a user.
        """
        return self.repository.get_user_dm_conversations(user.id)
    
    def edit_message(self, message_id: int, new_content: str, edited_by: User) -> Message:
        """
        Edit a message.
        
        Raises:
            ValueError: If message not found or user doesn't have permission
        """
        message = self.repository.get_message_by_id(message_id)
        if not message:
            raise ValueError('Message not found')
        
        if not message.can_edit(edited_by):
            raise ValueError('You do not have permission to edit this message')
        
        updated = self.repository.edit_message(message_id, new_content, edited_by.id)
        if not updated:
            raise ValueError('Failed to edit message')
        
        return updated
    
    def delete_message(self, message_id: int, deleted_by: User) -> Message:
        """
        Soft delete a message.
        
        Raises:
            ValueError: If message not found or user doesn't have permission
        """
        message = self.repository.get_message_by_id(message_id)
        if not message:
            raise ValueError('Message not found')
        
        if not message.can_delete(deleted_by):
            raise ValueError('You do not have permission to delete this message')
        
        deleted = self.repository.soft_delete_message(message_id, deleted_by.id)
        if not deleted:
            raise ValueError('Failed to delete message')
        
        return deleted
    
    def get_edit_history(self, message_id: int, user: User) -> List[MessageEditHistory]:
        """
        Get edit history for a message.
        
        Raises:
            ValueError: If message not found or user doesn't have access
        """
        message = self.repository.get_message_by_id(message_id)
        if not message:
            raise ValueError('Message not found')
        
        # Check access - same logic as viewing the message
        if message.channel:
            if not self._has_channel_access(user, message.channel_id):
                raise ValueError('You do not have access to this channel')
        elif message.is_dm:
            if user.id not in [message.sender_id, message.dm_recipient_id]:
                raise ValueError('You do not have access to this conversation')
        
        return self.repository.get_edit_history(message_id)
    
    def get_message(self, message_id: int, user: User) -> Message:
        """
        Get a single message.
        
        Raises:
            ValueError: If message not found or user doesn't have access
        """
        message = self.repository.get_message_by_id(message_id)
        if not message:
            raise ValueError('Message not found')
        
        # Check access
        if message.channel:
            if not self._has_channel_access(user, message.channel_id):
                raise ValueError('You do not have access to this channel')
        elif message.is_dm:
            if user.id not in [message.sender_id, message.dm_recipient_id]:
                raise ValueError('You do not have access to this conversation')
        
        return message
    
    def search_messages(self, query: str, user: User, channel_id: Optional[int] = None) -> List[Message]:
        """
        Search messages by content.
        """
        return self.repository.search_messages(query, user.id, channel_id)
