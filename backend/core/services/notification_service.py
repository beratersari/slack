"""
Notification service for business logic.
"""
import re
from typing import List, Optional, Dict, Any, Set
from django.utils import timezone
from core.models import (
    Notification, NotificationType, NotificationSettings,
    UnreadCount, KeywordAlert, ChannelMention,
    User, Channel, Workspace, Message
)
from core.repositories import (
    NotificationRepository, NotificationSettingsRepository,
    UnreadCountRepository, KeywordAlertRepository, ChannelMentionRepository,
    UserRepository, ChannelRepository
)


class NotificationService:
    """
    Service for notification-related business logic.
    Handles @mentions, @channel, @here, DMs, threads, keywords, etc.
    """

    def __init__(self):
        self.notification_repo = NotificationRepository()
        self.settings_repo = NotificationSettingsRepository()
        self.unread_repo = UnreadCountRepository()
        self.keyword_repo = KeywordAlertRepository()
        self.mention_repo = ChannelMentionRepository()
        self.user_repo = UserRepository()
        self.channel_repo = ChannelRepository()

    # ============================================
    # Main Entry Point - Process Message
    # ============================================

    def process_message_notifications(self, message: Message, sender: User) -> Dict[str, int]:
        """
        Process a new message and generate notifications for all relevant users.

        Returns:
            Dict with counts: {notifications_created, mentions, channel_mentions}
        """
        stats = {
            'notifications_created': 0,
            'mentions': 0,
            'channel_mentions': 0,
        }

        # Get message details
        channel = message.channel
        workspace = channel.workspace if channel else None
        content = message.content

        # Parse mentions from content
        mentioned_usernames = self._parse_username_mentions(content)
        has_channel_mention = '@channel' in content.lower()
        has_here_mention = '@here' in content.lower()
        has_everyone_mention = '@everyone' in content.lower()

        # Get recipients based on message type
        recipients = set()

        # 1. Direct Message
        if channel and channel.channel_type == 'direct':
            recipients = self._get_dm_recipients(channel, sender)
            stats['notifications_created'] += self._create_dm_notifications(
                message, sender, recipients
            )

        # 2. Thread Reply
        elif message.parent_message:
            recipients = self._get_thread_recipients(message, sender)
            stats['notifications_created'] += self._create_thread_notifications(
                message, sender, recipients
            )

        # 3. Channel Message with mentions
        elif channel:
            # Increment unread for all channel members
            self._increment_channel_unreads(channel, sender)

            # @username mentions
            if mentioned_usernames:
                mention_recipients = self._get_mentioned_users(
                    mentioned_usernames, channel
                )
                stats['notifications_created'] += self._create_mention_notifications(
                    message, sender, mention_recipients, NotificationType.MENTION
                )
                stats['mentions'] += len(mention_recipients)
                recipients.update(mention_recipients)

            # @channel, @here, @everyone
            if has_channel_mention or has_here_mention or has_everyone_mention:
                channel_recipients = self._get_channel_mention_recipients(
                    channel, sender, has_here_mention
                )
                mention_type = NotificationType.CHANNEL_MENTION if has_channel_mention else \
                              NotificationType.HERE_MENTION if has_here_mention else \
                              NotificationType.EVERYONE_MENTION

                stats['notifications_created'] += self._create_mention_notifications(
                    message, sender, channel_recipients, mention_type
                )
                stats['channel_mentions'] += len(channel_recipients)
                recipients.update(channel_recipients)

                # Track channel mention
                if has_channel_mention or has_here_mention or has_everyone_mention:
                    self._track_channel_mention(message, has_channel_mention, has_here_mention, has_everyone_mention)

            # Keyword alerts
            keyword_recipients = self._get_keyword_alert_recipients(content, workspace)
            if keyword_recipients:
                stats['notifications_created'] += self._create_keyword_notifications(
                    message, sender, keyword_recipients, content
                )

        # Create notifications for remaining recipients (channel members without specific mentions)
        if channel and not (has_channel_mention or has_here_mention or has_everyone_mention):
            # Notify channel members who have "all messages" setting
            channel_members = self._get_channel_members_for_notifications(channel, sender)
            # Filter out those already notified
            new_recipients = channel_members - recipients
            if new_recipients:
                stats['notifications_created'] += self._create_channel_message_notifications(
                    message, sender, new_recipients
                )

        return stats

    # ============================================
    # Mention Parsing
    # ============================================

    def _parse_username_mentions(self, content: str) -> List[str]:
        """Parse @username mentions from message content."""
        # Match @username (letters, numbers, underscores, hyphens)
        pattern = r'@([a-zA-Z0-9_-]+)'
        matches = re.findall(pattern, content)
        return matches

    def _parse_channel_mentions(self, content: str) -> List[str]:
        """Check for @channel, @here, @everyone mentions."""
        mentions = []
        content_lower = content.lower()
        if '@channel' in content_lower:
            mentions.append('channel')
        if '@here' in content_lower:
            mentions.append('here')
        if '@everyone' in content_lower:
            mentions.append('everyone')
        return mentions

    # ============================================
    # Recipient Determination
    # ============================================

    def _get_dm_recipients(self, channel: Channel, sender: User) -> Set[int]:
        """Get recipients for a DM."""
        recipients = set()
        if channel.channel_type == 'direct':
            # Get the other participant(s)
            from core.models import ChannelMembership
            members = ChannelMembership.objects.filter(channel=channel).values_list('user_id', flat=True)
            for user_id in members:
                if user_id != sender.id:
                    recipients.add(user_id)
        return recipients

    def _get_thread_recipients(self, message: Message, sender: User) -> Set[int]:
        """Get recipients for a thread reply."""
        recipients = set()

        # Get parent message and all replies
        parent = message.parent_message
        if parent:
            # Get all participants in thread
            from core.models import Message as MessageModel
            thread_messages = MessageModel.objects.filter(
                Q(id=parent.id) | Q(parent_message_id=parent.id)
            ).values_list('sender_id', flat=True)

            for user_id in set(thread_messages):
                if user_id != sender.id:
                    recipients.add(user_id)

            # Also include the parent message sender
            if parent.sender_id != sender.id:
                recipients.add(parent.sender_id)

        return recipients

    def _get_mentioned_users(self, usernames: List[str], channel: Channel) -> Set[int]:
        """Get user IDs from mentioned usernames."""
        recipients = set()
        for username in usernames:
            try:
                user = User.objects.get(username__iexact=username)
                # Only notify if user is in the channel/workspace
                if channel:
                    # Check if user is member of channel or workspace
                    from core.models import ChannelMembership, WorkspaceMembership
                    is_member = ChannelMembership.objects.filter(
                        channel=channel, user=user
                    ).exists() or WorkspaceMembership.objects.filter(
                        workspace=channel.workspace, user=user
                    ).exists()
                    if is_member:
                        recipients.add(user.id)
            except User.DoesNotExist:
                pass
        return recipients

    def _get_channel_mention_recipients(self, channel: Channel, sender: User,
                                        only_online: bool = False) -> Set[int]:
        """Get recipients for @channel, @here, @everyone mentions."""
        recipients = set()

        # Get all workspace members
        from core.models import WorkspaceMembership
        workspace_members = WorkspaceMembership.objects.filter(
            workspace=channel.workspace
        ).values_list('user_id', flat=True)

        for user_id in workspace_members:
            if user_id != sender.id:
                user = User.objects.get(id=user_id)
                if only_online:
                    # @here - only online users
                    if user.is_online:
                        recipients.add(user_id)
                else:
                    # @channel, @everyone - all workspace members
                    recipients.add(user_id)

        return recipients

    def _get_channel_members_for_notifications(self, channel: Channel,
                                               sender: User) -> Set[int]:
        """Get channel members who should receive notifications."""
        recipients = set()
        from core.models import ChannelMembership
        members = ChannelMembership.objects.filter(channel=channel).values_list('user_id', flat=True)

        for user_id in members:
            if user_id != sender.id:
                recipients.add(user_id)

        return recipients

    def _get_keyword_alert_recipients(self, content: str,
                                      workspace: Optional[Workspace]) -> Dict[int, List[str]]:
        """Get users who have keyword alerts matching this message."""
        recipients = {}  # {user_id: [matched_keywords]}

        if workspace:
            alerts = self.keyword_repo.find_matching_keywords(content, workspace.id)
            for alert in alerts:
                if alert.user_id not in recipients:
                    recipients[alert.user_id] = []
                recipients[alert.user_id].append(alert.keyword)

        return recipients

    # ============================================
    # Notification Creation
    # ============================================

    def _create_dm_notifications(self, message: Message, sender: User,
                                  recipients: Set[int]) -> int:
        """Create notifications for DM recipients."""
        count = 0
        for user_id in recipients:
            if self._should_notify(user_id, message.channel, NotificationType.DM):
                self.notification_repo.create_notification(
                    user_id=user_id,
                    notification_type=NotificationType.DM,
                    title=f"New message from {sender.full_name}",
                    body=message.content[:200],
                    link=f"/dm/{sender.id}",
                    message_id=message.id,
                    channel_id=message.channel_id,
                    workspace_id=message.channel.workspace_id if message.channel else None,
                    triggered_by_id=sender.id
                )
                count += 1
        return count

    def _create_thread_notifications(self, message: Message, sender: User,
                                      recipients: Set[int]) -> int:
        """Create notifications for thread reply recipients."""
        count = 0
        for user_id in recipients:
            if self._should_notify(user_id, message.channel, NotificationType.THREAD_REPLY):
                parent_sender = message.parent_message.sender if message.parent_message else None
                self.notification_repo.create_notification(
                    user_id=user_id,
                    notification_type=NotificationType.THREAD_REPLY,
                    title=f"New reply in thread",
                    body=message.content[:200],
                    link=f"/messages/{message.parent_message_id}",
                    message_id=message.id,
                    channel_id=message.channel_id,
                    workspace_id=message.channel.workspace_id if message.channel else None,
                    triggered_by_id=sender.id
                )
                count += 1
        return count

    def _create_mention_notifications(self, message: Message, sender: User,
                                       recipients: Set[int],
                                       notification_type: str) -> int:
        """Create notifications for @mentions."""
        count = 0
        for user_id in recipients:
            if self._should_notify(user_id, message.channel, notification_type):
                self.notification_repo.create_notification(
                    user_id=user_id,
                    notification_type=notification_type,
                    title=f"You were mentioned by {sender.full_name}",
                    body=message.content[:200],
                    link=f"/channels/{message.channel_id}/messages/{message.id}",
                    message_id=message.id,
                    channel_id=message.channel_id,
                    workspace_id=message.channel.workspace_id if message.channel else None,
                    triggered_by_id=sender.id
                )
                count += 1
        return count

    def _create_keyword_notifications(self, message: Message, sender: User,
                                       recipients: Dict[int, List[str]],
                                       content: str) -> int:
        """Create notifications for keyword alerts."""
        count = 0
        for user_id, keywords in recipients.items():
            if self._should_notify(user_id, message.channel, NotificationType.KEYWORD_ALERT):
                self.notification_repo.create_notification(
                    user_id=user_id,
                    notification_type=NotificationType.KEYWORD_ALERT,
                    title=f"Keyword mentioned by {sender.full_name}",
                    body=f"Matched: {', '.join(keywords)} - {content[:150]}",
                    link=f"/channels/{message.channel_id}/messages/{message.id}",
                    message_id=message.id,
                    channel_id=message.channel_id,
                    workspace_id=message.channel.workspace_id if message.channel else None,
                    triggered_by_id=sender.id
                )
                count += 1
        return count

    def _create_channel_message_notifications(self, message: Message, sender: User,
                                               recipients: Set[int]) -> int:
        """Create notifications for regular channel messages."""
        count = 0
        for user_id in recipients:
            if self._should_notify(user_id, message.channel, NotificationType.CHANNEL_MESSAGE):
                self.notification_repo.create_notification(
                    user_id=user_id,
                    notification_type=NotificationType.CHANNEL_MESSAGE,
                    title=f"New message in #{message.channel.name}",
                    body=f"{sender.full_name}: {message.content[:150]}",
                    link=f"/channels/{message.channel_id}/messages/{message.id}",
                    message_id=message.id,
                    channel_id=message.channel_id,
                    workspace_id=message.channel.workspace_id if message.channel else None,
                    triggered_by_id=sender.id
                )
                count += 1
        return count

    # ============================================
    # Notification Filtering
    # ============================================

    def _should_notify(self, user_id: int, channel: Optional[Channel],
                       notification_type: str) -> bool:
        """Check if user should receive this notification."""
        # Get settings
        settings = self.settings_repo.get_or_create_settings(user_id)

        # Check global toggle
        if not settings.all_notifications_enabled:
            return False

        # Check DND
        if settings.is_dnd_active():
            return False

        # Check channel muted
        if channel and settings.is_channel_muted(channel.id):
            return False

        # Check workspace muted
        if channel and settings.is_workspace_muted(channel.workspace_id):
            return False

        # Check type-specific settings
        if notification_type == NotificationType.MENTION:
            return settings.mention_notifications
        elif notification_type == NotificationType.DM:
            return settings.dm_notifications
        elif notification_type == NotificationType.THREAD_REPLY:
            return settings.thread_notifications != 'none'
        elif notification_type == NotificationType.REACTION:
            return settings.reaction_notifications
        elif notification_type == NotificationType.KEYWORD_ALERT:
            return settings.keyword_notifications
        elif notification_type in [
            NotificationType.CHANNEL_MENTION,
            NotificationType.HERE_MENTION,
            NotificationType.EVERYONE_MENTION,
        ]:
            return settings.channel_mention_notifications != 'none'

        return True

    # ============================================
    # Unread Count Management
    # ============================================

    def _increment_channel_unreads(self, channel: Channel, sender: User):
        """Increment unread count for all channel members except sender."""
        from core.models import ChannelMembership
        members = ChannelMembership.objects.filter(channel=channel).values_list('user_id', flat=True)

        for user_id in members:
            if user_id != sender.id:
                self.unread_repo.increment_unread(user_id, channel.id)

    def mark_channel_read(self, user_id: int, channel_id: int) -> bool:
        """Mark a channel as read for a user."""
        return self.unread_repo.reset_unread(user_id, channel_id)

    def get_unread_counts(self, user_id: int) -> Dict[str, Any]:
        """Get unread counts summary for a user."""
        unreads = self.unread_repo.get_user_unreads(user_id)
        total = sum(u.count for u in unreads)

        return {
            'total': total,
            'by_channel': [
                {'channel_id': u.channel_id, 'channel_name': u.channel.name, 'count': u.count}
                for u in unreads
            ]
        }

    # ============================================
    # Channel Mention Tracking
    # ============================================

    def _track_channel_mention(self, message: Message, has_channel: bool,
                                has_here: bool, has_everyone: bool):
        """Track @channel, @here, @everyone mentions."""
        if has_channel:
            self.mention_repo.create_mention(message.id, 'channel')
        if has_here:
            self.mention_repo.create_mention(message.id, 'here')
        if has_everyone:
            self.mention_repo.create_mention(message.id, 'everyone')

    # ============================================
    # Settings Management
    # ============================================

    def get_user_settings(self, user_id: int) -> NotificationSettings:
        """Get notification settings for a user."""
        return self.settings_repo.get_or_create_settings(user_id)

    def update_user_settings(self, user_id: int, **kwargs) -> NotificationSettings:
        """Update notification settings for a user."""
        return self.settings_repo.update_settings(user_id, **kwargs)

    def mute_channel(self, user_id: int, channel_id: int) -> bool:
        """Mute notifications for a channel."""
        return self.settings_repo.mute_channel(user_id, channel_id)

    def unmute_channel(self, user_id: int, channel_id: int) -> bool:
        """Unmute notifications for a channel."""
        return self.settings_repo.unmute_channel(user_id, channel_id)

    def set_dnd(self, user_id: int, enabled: bool, start: str = None,
                end: str = None) -> NotificationSettings:
        """Set Do Not Disturb for a user."""
        return self.settings_repo.update_settings(
            user_id,
            dnd_enabled=enabled,
            dnd_start_time=start,
            dnd_end_time=end
        )

    # ============================================
    # Keyword Alerts
    # ============================================

    def add_keyword_alert(self, user_id: int, keyword: str,
                         workspace_id: int = None) -> KeywordAlert:
        """Add a keyword alert for a user."""
        return self.keyword_repo.add_keyword(user_id, keyword, workspace_id)

    def remove_keyword_alert(self, user_id: int, keyword: str,
                            workspace_id: int = None) -> bool:
        """Remove a keyword alert."""
        return self.keyword_repo.remove_keyword(user_id, keyword, workspace_id)

    def get_user_keywords(self, user_id: int) -> List[KeywordAlert]:
        """Get all keyword alerts for a user."""
        return self.keyword_repo.get_user_keywords(user_id)
