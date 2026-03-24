"""
Notification models for the notification system.
"""
from django.db import models
from django.conf import settings
from .base import BaseModel


class NotificationType(models.TextChoices):
    """Types of notifications."""
    MENTION = 'mention', 'Mention'
    DM = 'dm', 'Direct Message'
    THREAD_REPLY = 'thread_reply', 'Thread Reply'
    REACTION = 'reaction', 'Reaction'
    CHANNEL_MESSAGE = 'channel_message', 'Channel Message'
    KEYWORD_ALERT = 'keyword_alert', 'Keyword Alert'
    CHANNEL_MENTION = 'channel_mention', '@channel'
    HERE_MENTION = 'here_mention', '@here'
    EVERYONE_MENTION = 'everyone_mention', '@everyone'
    WORKSPACE_INVITE = 'workspace_invite', 'Workspace Invite'
    CHANNEL_INVITE = 'channel_invite', 'Channel Invite'


class Notification(BaseModel):
    """
    A notification record for a user.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    # Type of notification
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        default=NotificationType.MENTION
    )

    # Content
    title = models.CharField(max_length=200)
    body = models.TextField(max_length=500, blank=True)

    # Link to navigate to (message, channel, etc.)
    link = models.CharField(max_length=500, blank=True)

    # Related objects
    message = models.ForeignKey(
        'Message',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    channel = models.ForeignKey(
        'Channel',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    workspace = models.ForeignKey(
        'Workspace',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='triggered_notifications'
    )

    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['notification_type']),
        ]

    def __str__(self):
        return f"{self.notification_type} for {self.user.username}: {self.title}"

    @property
    def is_mention_type(self):
        """Check if this is a mention notification."""
        return self.notification_type in [
            NotificationType.MENTION,
            NotificationType.CHANNEL_MENTION,
            NotificationType.HERE_MENTION,
            NotificationType.EVERYONE_MENTION,
        ]


class NotificationSettings(BaseModel):
    """
    User notification preferences.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_settings'
    )

    # Global toggles
    all_notifications_enabled = models.BooleanField(default=True)
    desktop_notifications = models.BooleanField(default=True)
    mobile_notifications = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    sound_enabled = models.BooleanField(default=True)

    # Per-type settings
    mention_notifications = models.BooleanField(default=True)
    dm_notifications = models.BooleanField(default=True)
    thread_notifications = models.CharField(
        max_length=20,
        default='all',
        choices=[
            ('all', 'All messages'),
            ('mentions', 'Only @mentions'),
            ('none', 'Nothing'),
        ]
    )
    reaction_notifications = models.BooleanField(default=True)
    keyword_notifications = models.BooleanField(default=True)

    # @channel, @here, @everyone settings
    channel_mention_notifications = models.CharField(
        max_length=20,
        default='mentions',
        choices=[
            ('all', 'All messages'),
            ('mentions', 'Only @mentions'),
            ('none', 'Nothing'),
        ]
    )

    # Do Not Disturb
    dnd_enabled = models.BooleanField(default=False)
    dnd_start_time = models.TimeField(null=True, blank=True, default='22:00')
    dnd_end_time = models.TimeField(null=True, blank=True, default='08:00')

    # Email preferences
    email_digest_frequency = models.CharField(
        max_length=20,
        default='off',
        choices=[
            ('off', 'Off'),
            ('hourly', 'Hourly'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
        ]
    )

    # Muted channels/workspaces
    muted_channels = models.ManyToManyField(
        'Channel',
        blank=True,
        related_name='muted_by'
    )
    muted_workspaces = models.ManyToManyField(
        'Workspace',
        blank=True,
        related_name='muted_by'
    )

    class Meta:
        db_table = 'notification_settings'

    def __str__(self):
        return f"Notification settings for {self.user.username}"

    def is_dnd_active(self):
        """Check if DND is currently active."""
        if not self.dnd_enabled:
            return False

        from datetime import datetime
        now = datetime.now().time()

        if self.dnd_start_time and self.dnd_end_time:
            if self.dnd_start_time <= self.dnd_end_time:
                return self.dnd_start_time <= now <= self.dnd_end_time
            else:
                # Overnight DND (e.g., 22:00 to 08:00)
                return now >= self.dnd_start_time or now <= self.dnd_end_time

        return False

    def is_channel_muted(self, channel_id):
        """Check if a channel is muted."""
        return self.muted_channels.filter(id=channel_id).exists()

    def is_workspace_muted(self, workspace_id):
        """Check if a workspace is muted."""
        return self.muted_workspaces.filter(id=workspace_id).exists()


class UnreadCount(BaseModel):
    """
    Per-channel unread message count for a user.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='unread_counts'
    )
    channel = models.ForeignKey(
        'Channel',
        on_delete=models.CASCADE,
        related_name='unread_counts'
    )

    count = models.PositiveIntegerField(default=0)
    last_read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'unread_counts'
        unique_together = ['user', 'channel']
        indexes = [
            models.Index(fields=['user', 'count']),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.count} unread in {self.channel.name}"


class KeywordAlert(BaseModel):
    """
    User's keyword alert subscriptions.
    When someone mentions a keyword, the user gets notified.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='keyword_alerts'
    )
    keyword = models.CharField(max_length=100)
    workspace = models.ForeignKey(
        'Workspace',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='keyword_alerts'
    )

    # Notification preferences for this keyword
    notify_on_match = models.BooleanField(default=True)

    class Meta:
        db_table = 'keyword_alerts'
        unique_together = ['user', 'keyword', 'workspace']
        indexes = [
            models.Index(fields=['user', 'keyword']),
        ]

    def __str__(self):
        return f"{self.user.username} alerts for '{self.keyword}'"


class ChannelMention(BaseModel):
    """
    Tracks @channel, @here, @everyone mentions in messages.
    Used to determine who should be notified.
    """
    message = models.ForeignKey(
        'Message',
        on_delete=models.CASCADE,
        related_name='channel_mentions'
    )
    mention_type = models.CharField(
        max_length=20,
        choices=[
            ('channel', '@channel'),
            ('here', '@here'),
            ('everyone', '@everyone'),
        ]
    )
    notified_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='channel_mention_notifications'
    )

    class Meta:
        db_table = 'channel_mentions'

    def __str__(self):
        return f"{self.mention_type} in message {self.message.id}"
