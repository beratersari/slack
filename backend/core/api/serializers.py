"""
Serializers for API request/response handling.
"""
from rest_framework import serializers
from core.models import User, UserType, Workspace, WorkspaceMembership, WorkspaceRole
from core.models import Channel, ChannelMembership, ChannelRole, ChannelType
from core.models import ChannelSection, ChannelSectionItem
from core.models import Message, MessageEditHistory
from core.models import MessageReaction, CustomEmoji
from core.models import Notification, NotificationType, NotificationSettings, UnreadCount, KeywordAlert, ChannelMention


class UserTypeSerializer(serializers.Serializer):
    """Serializer for user type choices."""
    value = serializers.CharField()
    label = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    
    Includes presence information (like Slack):
    - last_seen: When the user was last active
    - is_online: Whether user is currently online (active within 5 min)
    - presence_display: Human-readable presence like "Active", "Last seen 10 min ago"
    """
    full_name = serializers.ReadOnlyField()
    user_type_display = serializers.CharField(source='get_user_type_display', read_only=True)
    is_online = serializers.ReadOnlyField()
    presence_display = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'full_name', 'user_type', 'user_type_display',
            'avatar', 'phone', 'job_title', 'department',
            'status_message', 'timezone',
            'is_active', 'is_staff',
            'last_seen', 'is_online', 'presence_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_staff', 'last_seen', 'is_online', 'presence_display']


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users.
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'username', 'password', 'password_confirm',
            'first_name', 'last_name', 'user_type',
            'avatar', 'phone', 'job_title', 'department',
            'status_message', 'timezone'
        ]
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        return data
    
    def validate_user_type(self, value):
        valid_types = [t.value for t in UserType]
        if value not in valid_types:
            raise serializers.ValidationError(
                f'Invalid user type. Must be one of: {", ".join(valid_types)}'
            )
        return value


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user information.
    """
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'avatar', 'phone',
            'job_title', 'department', 'status_message', 'timezone'
        ]


class LoginSerializer(serializers.Serializer):
    """
    Serializer for login request.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class LoginResponseSerializer(serializers.Serializer):
    """
    Serializer for login response.
    """
    user = UserSerializer()
    token = serializers.CharField()


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'username', 'password', 'password_confirm',
            'first_name', 'last_name'
        ]
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        return data


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change request.
    """
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Passwords do not match.'
            })
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset request.
    """
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation.
    """
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Passwords do not match.'
            })
        return data


class TokenRefreshSerializer(serializers.Serializer):
    """
    Serializer for token refresh request.
    """
    token = serializers.CharField()


class ErrorResponseSerializer(serializers.Serializer):
    """
    Serializer for error responses.
    """
    error = serializers.CharField()
    details = serializers.DictField(required=False)


class SuccessResponseSerializer(serializers.Serializer):
    """
    Serializer for success responses.
    """
    message = serializers.CharField()
    data = serializers.DictField(required=False)


# ============================================
# Workspace Serializers
# ============================================

class WorkspaceRoleSerializer(serializers.Serializer):
    """Serializer for workspace role choices."""
    value = serializers.CharField()
    label = serializers.CharField()


class WorkspaceMembershipSerializer(serializers.ModelSerializer):
    """
    Serializer for workspace membership.
    """
    user = UserSerializer(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = WorkspaceMembership
        fields = [
            'id', 'user', 'role', 'role_display',
            'notifications_enabled', 'is_favorite', 'display_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WorkspaceSerializer(serializers.ModelSerializer):
    """
    Serializer for Workspace model.
    """
    owner = UserSerializer(read_only=True)
    member_count = serializers.ReadOnlyField()

    class Meta:
        model = Workspace
        fields = [
            'id', 'name', 'description', 'icon',
            'owner', 'is_private', 'is_active',
            'workspace_url', 'member_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner']


class WorkspaceCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new workspace.
    """
    class Meta:
        model = Workspace
        fields = [
            'name', 'description', 'icon',
            'is_private', 'workspace_url'
        ]


class WorkspaceUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a workspace.
    """
    class Meta:
        model = Workspace
        fields = [
            'name', 'description', 'icon',
            'is_private', 'workspace_url', 'is_active'
        ]


class WorkspaceAddMemberSerializer(serializers.Serializer):
    """
    Serializer for adding a member to a workspace.
    """
    user_id = serializers.IntegerField()
    role = serializers.ChoiceField(
        choices=WorkspaceRole.choices(),
        default=WorkspaceRole.MEMBER.value
    )


class WorkspaceMembershipUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating workspace membership.
    """
    role = serializers.ChoiceField(choices=WorkspaceRole.choices())


# ============================================
# Channel Serializers
# ============================================

class ChannelTypeSerializer(serializers.Serializer):
    """Serializer for channel type choices."""
    value = serializers.CharField()
    label = serializers.CharField()


class ChannelRoleSerializer(serializers.Serializer):
    """Serializer for channel role choices."""
    value = serializers.CharField()
    label = serializers.CharField()


class ChannelMembershipSerializer(serializers.ModelSerializer):
    """
    Serializer for channel membership.
    """
    user = UserSerializer(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = ChannelMembership
        fields = [
            'id', 'user', 'role', 'role_display',
            'notifications_enabled', 'is_favorite', 'is_muted',
            'last_read_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChannelSerializer(serializers.ModelSerializer):
    """
    Serializer for Channel model.
    """
    workspace = WorkspaceSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    member_count = serializers.ReadOnlyField()
    channel_type_display = serializers.CharField(source='get_channel_type_display', read_only=True)

    class Meta:
        model = Channel
        fields = [
            'id', 'name', 'description', 'topic',
            'workspace', 'created_by', 'channel_type', 'channel_type_display',
            'is_active', 'is_archived', 'member_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'workspace', 'created_by']


class ChannelListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for channel list views.
    Only includes essential fields - no nested objects.
    """
    workspace_id = serializers.IntegerField(source='workspace.id', read_only=True)
    workspace_name = serializers.CharField(source='workspace.name', read_only=True)
    member_count = serializers.ReadOnlyField()
    is_dm = serializers.SerializerMethodField()

    class Meta:
        model = Channel
        fields = [
            'id', 'name', 'description', 'topic',
            'workspace_id', 'workspace_name',
            'channel_type', 'is_active', 'is_archived',
            'member_count', 'is_dm'
        ]

    def get_is_dm(self, obj):
        return obj.channel_type == 'direct'


class ChannelDetailSerializer(serializers.ModelSerializer):
    """
    Medium-weight serializer for channel detail views.
    Includes minimal nested data.
    """
    workspace_id = serializers.IntegerField(source='workspace.id', read_only=True)
    workspace_name = serializers.CharField(source='workspace.name', read_only=True)
    created_by_id = serializers.IntegerField(source='created_by.id', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    member_count = serializers.ReadOnlyField()
    channel_type_display = serializers.CharField(source='get_channel_type_display', read_only=True)

    class Meta:
        model = Channel
        fields = [
            'id', 'name', 'description', 'topic',
            'workspace_id', 'workspace_name',
            'created_by_id', 'created_by_name',
            'channel_type', 'channel_type_display',
            'is_active', 'is_archived', 'member_count',
            'created_at', 'updated_at'
        ]


class ChannelMembershipListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing channel members.
    Only essential user info.
    """
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_avatar = serializers.ImageField(source='user.avatar', read_only=True, allow_null=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = ChannelMembership
        fields = [
            'id', 'user_id', 'user_email', 'user_name', 'user_avatar',
            'role', 'role_display', 'notifications_enabled', 'is_muted',
            'last_read_at'
        ]


class ChannelCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new channel.
    """
    workspace_id = serializers.IntegerField()

    class Meta:
        model = Channel
        fields = [
            'name', 'description', 'topic',
            'workspace_id', 'channel_type'
        ]


class ChannelUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a channel.
    """
    class Meta:
        model = Channel
        fields = [
            'name', 'description', 'topic',
            'is_archived'
        ]


class ChannelAddMemberSerializer(serializers.Serializer):
    """
    Serializer for adding a member to a channel.
    """
    user_id = serializers.IntegerField()
    role = serializers.ChoiceField(
        choices=ChannelRole.choices(),
        default=ChannelRole.MEMBER.value
    )


class DirectMessageSerializer(serializers.Serializer):
    """
    Serializer for creating/starting a direct message.
    """
    user_id = serializers.IntegerField(help_text="ID of the user to DM")
    workspace_id = serializers.IntegerField(help_text="ID of the workspace context")


# ============================================
# Message Serializers
# ============================================

class MessageEditHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for message edit history.
    """
    edited_by = UserSerializer(read_only=True)
    
    class Meta:
        model = MessageEditHistory
        fields = [
            'id', 'old_content', 'edited_by', 'edited_at'
        ]


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for Message model.
    
    Includes:
    - Sender info
    - Thread info (parent message, reply count)
    - Edit info (is_edited, edited_at)
    - Soft delete status
    """
    sender = UserSerializer(read_only=True)
    channel = ChannelSerializer(read_only=True)
    dm_recipient = UserSerializer(read_only=True)
    parent_message_id = serializers.PrimaryKeyRelatedField(
        source='parent_message',
        read_only=True,
        allow_null=True
    )
    reply_count = serializers.ReadOnlyField()
    is_thread_parent = serializers.ReadOnlyField()
    is_reply = serializers.ReadOnlyField()
    is_dm = serializers.ReadOnlyField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'content', 'sender', 'channel', 'dm_recipient',
            'parent_message_id', 'reply_count', 'is_thread_parent', 'is_reply', 'is_dm',
            'is_edited', 'edited_at',
            'is_deleted', 'deleted_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'sender', 'channel', 'dm_recipient', 'parent_message_id',
            'is_edited', 'edited_at', 'is_deleted', 'deleted_at',
            'created_at', 'updated_at'
        ]


class MessageListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for message list views.
    Only includes essential fields - no nested objects.
    """
    sender_id = serializers.IntegerField(source='sender.id', read_only=True)
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    sender_avatar = serializers.ImageField(source='sender.avatar', read_only=True, allow_null=True)
    channel_id = serializers.IntegerField(source='channel.id', read_only=True)
    dm_recipient_id = serializers.IntegerField(source='dm_recipient.id', read_only=True, allow_null=True)
    dm_recipient_name = serializers.CharField(source='dm_recipient.full_name', read_only=True, allow_null=True)
    parent_message_id = serializers.PrimaryKeyRelatedField(
        source='parent_message',
        read_only=True,
        allow_null=True
    )
    reply_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'content',
            'sender_id', 'sender_name', 'sender_avatar',
            'channel_id',
            'dm_recipient_id', 'dm_recipient_name',
            'parent_message_id', 'reply_count',
            'is_edited', 'edited_at',
            'is_deleted', 'deleted_at',
            'created_at', 'updated_at'
        ]


class MessageDetailSerializer(MessageSerializer):
    """
    Detailed message serializer with edit history and thread replies.
    Use this when you need full message details including the thread.
    """
    edit_history = MessageEditHistorySerializer(many=True, read_only=True)
    replies = MessageListSerializer(many=True, read_only=True)
    
    class Meta(MessageSerializer.Meta):
        fields = MessageSerializer.Meta.fields + ['edit_history', 'replies']


class MessageThreadSerializer(MessageSerializer):
    """
    Serializer for message with thread replies.
    (Kept for backward compatibility - MessageDetailSerializer now includes replies)
    """
    replies = MessageListSerializer(many=True, read_only=True)
    
    class Meta(MessageSerializer.Meta):
        fields = MessageSerializer.Meta.fields + ['replies']


class MessageCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a channel message.
    """
    content = serializers.CharField(max_length=10000)


class DirectMessageCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a direct message.
    recipient_id is taken from URL, not required in body.
    """
    content = serializers.CharField(max_length=10000)


class MessageReplySerializer(serializers.Serializer):
    """
    Serializer for replying to a message (creating a thread).
    """
    content = serializers.CharField(max_length=10000)


class MessageEditSerializer(serializers.Serializer):
    """
    Serializer for editing a message.
    """
    content = serializers.CharField(max_length=10000)


class DMConversationSerializer(serializers.Serializer):
    """
    Serializer for DM conversation list item.
    """
    user = UserSerializer()
    last_message = MessageSerializer()
    unread_count = serializers.IntegerField()


# ============================================
# Channel Section Serializers
# ============================================

class ChannelSectionItemSerializer(serializers.ModelSerializer):
    """
    Serializer for ChannelSectionItem model.
    Includes channel details.
    """
    channel = ChannelSerializer(read_only=True)

    class Meta:
        model = ChannelSectionItem
        fields = [
            'id', 'section', 'channel', 'order',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChannelSectionSerializer(serializers.ModelSerializer):
    """
    Serializer for ChannelSection model.
    Includes items (channels) in the section.
    """
    items = ChannelSectionItemSerializer(many=True, read_only=True)
    channel_count = serializers.ReadOnlyField()

    class Meta:
        model = ChannelSection
        fields = [
            'id', 'name', 'user', 'workspace',
            'order', 'color', 'section_type', 'is_collapsed',
            'channel_count', 'items',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'section_type', 'created_at', 'updated_at']


class ChannelSectionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new channel section.
    """
    class Meta:
        model = ChannelSection
        fields = ['name', 'color', 'order']


class ChannelSectionUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a channel section.
    """
    class Meta:
        model = ChannelSection
        fields = ['name', 'color', 'order', 'is_collapsed']


class ChannelSectionReorderSerializer(serializers.Serializer):
    """
    Serializer for reordering sections.
    Expects a dict mapping section_id to new order.
    """
    section_orders = serializers.DictField(
        child=serializers.IntegerField(),
        help_text="Dict mapping section_id to new order value"
    )


class AddChannelToSectionSerializer(serializers.Serializer):
    """
    Serializer for adding a channel to a section.
    """
    channel_id = serializers.IntegerField()
    order = serializers.IntegerField(default=0)


class ReorderChannelsSerializer(serializers.Serializer):
    """
    Serializer for reordering channels within a section.
    Expects a dict mapping item_id to new order.
    """
    item_orders = serializers.DictField(
        child=serializers.IntegerField(),
        help_text="Dict mapping item_id to new order value"
    )


class MoveChannelSerializer(serializers.Serializer):
    """
    Serializer for moving a channel from one section to another.
    """
    from_section_id = serializers.IntegerField()
    to_section_id = serializers.IntegerField()
    order = serializers.IntegerField(default=0)


# ============================================
# Emoji Serializers
# ============================================

class MessageReactionSerializer(serializers.ModelSerializer):
    """
    Serializer for MessageReaction model.
    """
    user = UserSerializer(read_only=True)
    is_custom_emoji = serializers.ReadOnlyField()

    class Meta:
        model = MessageReaction
        fields = [
            'id', 'message', 'user', 'emoji',
            'custom_emoji', 'is_custom_emoji',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'is_custom_emoji', 'created_at', 'updated_at']


class ReactionSummarySerializer(serializers.Serializer):
    """
    Serializer for reaction summary (emoji + count + users).
    """
    emoji = serializers.CharField()
    count = serializers.IntegerField()
    users = serializers.ListField(child=serializers.IntegerField())
    has_custom = serializers.BooleanField()
    custom_emoji_id = serializers.IntegerField(required=False, allow_null=True)


class MessageReactionsResponseSerializer(serializers.Serializer):
    """
    Serializer for message reactions response.
    """
    reactions = ReactionSummarySerializer(many=True)
    total_count = serializers.IntegerField()


class AddReactionSerializer(serializers.Serializer):
    """
    Serializer for adding a reaction to a message.
    """
    emoji = serializers.CharField(
        max_length=50,
        help_text="Unicode emoji (👍) or custom shortcode (:party-parrot:)"
    )


class CustomEmojiSerializer(serializers.ModelSerializer):
    """
    Serializer for CustomEmoji model.
    """
    created_by = UserSerializer(read_only=True)
    shortcode = serializers.ReadOnlyField()
    is_alias = serializers.ReadOnlyField()

    class Meta:
        model = CustomEmoji
        fields = [
            'id', 'name', 'shortcode', 'image',
            'workspace', 'created_by',
            'alias_for', 'is_alias',
            'usage_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'shortcode', 'is_alias', 'usage_count', 'created_at', 'updated_at']


class CustomEmojiCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a custom emoji.
    """
    name = serializers.CharField(
        max_length=50,
        help_text="Emoji shortcode without colons, e.g., 'party-parrot'"
    )
    image = serializers.ImageField(
        help_text="Emoji image file (PNG, GIF, JPG, max 128x128 recommended)"
    )


class CustomEmojiAliasSerializer(serializers.Serializer):
    """
    Serializer for creating an emoji alias.
    """
    alias_name = serializers.CharField(
        max_length=50,
        help_text="New shortcode for the alias"
    )
    original_emoji_id = serializers.IntegerField(
        help_text="ID of the emoji to create alias for"
    )


# ============================================
# Notification Serializers
# ============================================

class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification model.
    """
    triggered_by = UserSerializer(read_only=True)
    channel = ChannelSerializer(read_only=True)
    workspace = WorkspaceSerializer(read_only=True)
    message = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'notification_type', 'title', 'body', 'link',
            'message', 'channel', 'workspace', 'triggered_by',
            'is_read', 'read_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class NotificationListSerializer(serializers.Serializer):
    """
    Serializer for notification list response.
    """
    notifications = NotificationSerializer(many=True)
    unread_count = serializers.IntegerField()
    total_count = serializers.IntegerField()


class NotificationSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for NotificationSettings model.
    """
    muted_channels = ChannelSerializer(many=True, read_only=True)
    muted_workspaces = WorkspaceSerializer(many=True, read_only=True)

    class Meta:
        model = NotificationSettings
        fields = [
            'id', 'user',
            'all_notifications_enabled', 'desktop_notifications',
            'mobile_notifications', 'email_notifications', 'sound_enabled',
            'mention_notifications', 'dm_notifications', 'thread_notifications',
            'reaction_notifications', 'keyword_notifications',
            'channel_mention_notifications',
            'dnd_enabled', 'dnd_start_time', 'dnd_end_time',
            'email_digest_frequency',
            'muted_channels', 'muted_workspaces',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class NotificationSettingsUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating notification settings.
    """
    all_notifications_enabled = serializers.BooleanField(required=False)
    desktop_notifications = serializers.BooleanField(required=False)
    mobile_notifications = serializers.BooleanField(required=False)
    email_notifications = serializers.BooleanField(required=False)
    sound_enabled = serializers.BooleanField(required=False)
    mention_notifications = serializers.BooleanField(required=False)
    dm_notifications = serializers.BooleanField(required=False)
    thread_notifications = serializers.ChoiceField(
        choices=['all', 'mentions', 'none'],
        required=False
    )
    reaction_notifications = serializers.BooleanField(required=False)
    keyword_notifications = serializers.BooleanField(required=False)
    channel_mention_notifications = serializers.ChoiceField(
        choices=['all', 'mentions', 'none'],
        required=False
    )
    dnd_enabled = serializers.BooleanField(required=False)
    dnd_start_time = serializers.TimeField(required=False)
    dnd_end_time = serializers.TimeField(required=False)
    email_digest_frequency = serializers.ChoiceField(
        choices=['off', 'hourly', 'daily', 'weekly'],
        required=False
    )


class UnreadCountSerializer(serializers.ModelSerializer):
    """
    Serializer for UnreadCount model.
    """
    channel = ChannelSerializer(read_only=True)

    class Meta:
        model = UnreadCount
        fields = ['id', 'user', 'channel', 'count', 'last_read_at', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class UnreadSummarySerializer(serializers.Serializer):
    """
    Serializer for unread count summary.
    """
    total = serializers.IntegerField()
    by_channel = serializers.ListField(
        child=serializers.DictField()
    )


class KeywordAlertSerializer(serializers.ModelSerializer):
    """
    Serializer for KeywordAlert model.
    """
    class Meta:
        model = KeywordAlert
        fields = ['id', 'user', 'keyword', 'workspace', 'notify_on_match', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class KeywordAlertCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a keyword alert.
    """
    keyword = serializers.CharField(max_length=100)
    workspace_id = serializers.IntegerField(required=False)


class MarkNotificationReadSerializer(serializers.Serializer):
    """
    Serializer for marking notifications as read.
    """
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of notification IDs to mark as read. Empty = mark all."
    )

