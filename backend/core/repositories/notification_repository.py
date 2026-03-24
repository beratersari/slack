"""
Notification repository for database operations.
"""
from typing import List, Optional, Dict
from django.db.models import Q, Count, F
from core.models import (
    Notification, NotificationSettings, UnreadCount,
    KeywordAlert, ChannelMention, User, Channel, Workspace, Message
)
from .base_repository import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    """
    Repository for Notification model.
    """

    def __init__(self):
        super().__init__(Notification)

    def get_user_notifications(self, user_id: int, unread_only: bool = False,
                               limit: int = 50) -> List[Notification]:
        """Get notifications for a user."""
        queryset = Notification.objects.filter(user_id=user_id)
        if unread_only:
            queryset = queryset.filter(is_read=False)
        return list(queryset.select_related(
            'message', 'channel', 'workspace', 'triggered_by'
        ).order_by('-created_at')[:limit])

    def get_unread_count(self, user_id: int) -> int:
        """Get total unread notifications for a user."""
        return Notification.objects.filter(user_id=user_id, is_read=False).count()

    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Mark a notification as read."""
        from django.utils import timezone
        updated = Notification.objects.filter(
            id=notification_id,
            user_id=user_id
        ).update(is_read=True, read_at=timezone.now())
        return updated > 0

    def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user."""
        from django.utils import timezone
        updated = Notification.objects.filter(
            user_id=user_id,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        return updated

    def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """Delete a notification."""
        deleted, _ = Notification.objects.filter(
            id=notification_id,
            user_id=user_id
        ).delete()
        return deleted > 0

    def create_notification(self, user_id: int, notification_type: str,
                           title: str, body: str = '', link: str = '',
                           message_id: int = None, channel_id: int = None,
                           workspace_id: int = None, triggered_by_id: int = None) -> Notification:
        """Create a new notification."""
        return self.create(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            body=body,
            link=link,
            message_id=message_id,
            channel_id=channel_id,
            workspace_id=workspace_id,
            triggered_by_id=triggered_by_id
        )

    def bulk_create_notifications(self, notifications_data: List[Dict]) -> int:
        """Create multiple notifications at once."""
        notifications = [Notification(**data) for data in notifications_data]
        created = Notification.objects.bulk_create(notifications, batch_size=100)
        return len(created)

    def get_notifications_by_type(self, user_id: int, notification_type: str,
                                  limit: int = 20) -> List[Notification]:
        """Get notifications of a specific type."""
        return list(Notification.objects.filter(
            user_id=user_id,
            notification_type=notification_type
        ).select_related('message', 'channel').order_by('-created_at')[:limit])


class NotificationSettingsRepository(BaseRepository[NotificationSettings]):
    """
    Repository for NotificationSettings model.
    """

    def __init__(self):
        super().__init__(NotificationSettings)

    def get_or_create_settings(self, user_id: int) -> NotificationSettings:
        """Get or create notification settings for a user."""
        settings, created = NotificationSettings.objects.get_or_create(
            user_id=user_id,
            defaults={
                'all_notifications_enabled': True,
                'desktop_notifications': True,
                'mobile_notifications': True,
                'email_notifications': True,
            }
        )
        return settings

    def update_settings(self, user_id: int, **kwargs) -> Optional[NotificationSettings]:
        """Update notification settings."""
        settings = self.get_or_create_settings(user_id)
        for key, value in kwargs.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        settings.save()
        return settings

    def mute_channel(self, user_id: int, channel_id: int) -> bool:
        """Mute a channel for a user."""
        settings = self.get_or_create_settings(user_id)
        settings.muted_channels.add(channel_id)
        return True

    def unmute_channel(self, user_id: int, channel_id: int) -> bool:
        """Unmute a channel for a user."""
        settings = self.get_or_create_settings(user_id)
        settings.muted_channels.remove(channel_id)
        return True

    def mute_workspace(self, user_id: int, workspace_id: int) -> bool:
        """Mute a workspace for a user."""
        settings = self.get_or_create_settings(user_id)
        settings.muted_workspaces.add(workspace_id)
        return True

    def unmute_workspace(self, user_id: int, workspace_id: int) -> bool:
        """Unmute a workspace for a user."""
        settings = self.get_or_create_settings(user_id)
        settings.muted_workspaces.remove(workspace_id)
        return True


class UnreadCountRepository(BaseRepository[UnreadCount]):
    """
    Repository for UnreadCount model.
    """

    def __init__(self):
        super().__init__(UnreadCount)

    def get_user_unreads(self, user_id: int) -> List[UnreadCount]:
        """Get all unread counts for a user."""
        return list(UnreadCount.objects.filter(
            user_id=user_id,
            count__gt=0
        ).select_related('channel'))

    def get_channel_unread(self, user_id: int, channel_id: int) -> Optional[UnreadCount]:
        """Get unread count for a specific channel."""
        try:
            return UnreadCount.objects.get(user_id=user_id, channel_id=channel_id)
        except UnreadCount.DoesNotExist:
            return None

    def increment_unread(self, user_id: int, channel_id: int) -> UnreadCount:
        """Increment unread count for a channel."""
        unread, created = UnreadCount.objects.get_or_create(
            user_id=user_id,
            channel_id=channel_id,
            defaults={'count': 1}
        )
        if not created:
            unread.count = F('count') + 1
            unread.save(update_fields=['count'])
            unread.refresh_from_db()
        return unread

    def reset_unread(self, user_id: int, channel_id: int) -> bool:
        """Reset unread count for a channel."""
        from django.utils import timezone
        updated = UnreadCount.objects.filter(
            user_id=user_id,
            channel_id=channel_id
        ).update(count=0, last_read_at=timezone.now())
        return updated > 0

    def reset_all_unreads(self, user_id: int) -> int:
        """Reset all unread counts for a user."""
        from django.utils import timezone
        updated = UnreadCount.objects.filter(
            user_id=user_id
        ).update(count=0, last_read_at=timezone.now())
        return updated

    def get_total_unread(self, user_id: int) -> int:
        """Get total unread count across all channels."""
        result = UnreadCount.objects.filter(
            user_id=user_id
        ).aggregate(total=Count('count'))
        return result.get('total', 0) or 0


class KeywordAlertRepository(BaseRepository[KeywordAlert]):
    """
    Repository for KeywordAlert model.
    """

    def __init__(self):
        super().__init__(KeywordAlert)

    def get_user_keywords(self, user_id: int) -> List[KeywordAlert]:
        """Get all keyword alerts for a user."""
        return list(KeywordAlert.objects.filter(user_id=user_id))

    def get_workspace_keywords(self, user_id: int, workspace_id: int) -> List[KeywordAlert]:
        """Get keyword alerts for a user in a workspace."""
        return list(KeywordAlert.objects.filter(
            user_id=user_id
        ).filter(
            Q(workspace_id=workspace_id) | Q(workspace_id__isnull=True)
        ))

    def add_keyword(self, user_id: int, keyword: str,
                   workspace_id: int = None) -> KeywordAlert:
        """Add a keyword alert."""
        return self.create(
            user_id=user_id,
            keyword=keyword.lower().strip(),
            workspace_id=workspace_id
        )

    def remove_keyword(self, user_id: int, keyword: str,
                      workspace_id: int = None) -> bool:
        """Remove a keyword alert."""
        deleted, _ = KeywordAlert.objects.filter(
            user_id=user_id,
            keyword=keyword.lower().strip(),
            workspace_id=workspace_id
        ).delete()
        return deleted > 0

    def find_matching_keywords(self, text: str, workspace_id: int) -> List[KeywordAlert]:
        """Find keyword alerts that match the given text."""
        keywords = KeywordAlert.objects.filter(
            Q(workspace_id=workspace_id) | Q(workspace_id__isnull=True),
            notify_on_match=True
        ).select_related('user')

        matches = []
        text_lower = text.lower()
        for alert in keywords:
            if alert.keyword.lower() in text_lower:
                matches.append(alert)

        return matches


class ChannelMentionRepository(BaseRepository[ChannelMention]):
    """
    Repository for ChannelMention model.
    """

    def __init__(self):
        super().__init__(ChannelMention)

    def create_mention(self, message_id: int, mention_type: str,
                      user_ids: List[int] = None) -> ChannelMention:
        """Create a channel mention record."""
        mention = self.create(
            message_id=message_id,
            mention_type=mention_type
        )
        if user_ids:
            mention.notified_users.set(user_ids)
        return mention

    def get_message_mentions(self, message_id: int) -> Optional[ChannelMention]:
        """Get channel mention for a message."""
        try:
            return ChannelMention.objects.get(message_id=message_id)
        except ChannelMention.DoesNotExist:
            return None

    def mark_users_notified(self, mention_id: int, user_ids: List[int]) -> bool:
        """Mark users as notified for a channel mention."""
        try:
            mention = ChannelMention.objects.get(id=mention_id)
            mention.notified_users.add(*user_ids)
            return True
        except ChannelMention.DoesNotExist:
            return False
