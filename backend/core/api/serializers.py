"""
Serializers for API request/response handling.
"""
from rest_framework import serializers
from core.models import User, UserType, Group, GroupMembership, GroupRole
from core.models import Channel, ChannelMembership, ChannelRole, ChannelType
from core.models import Message, MessageEditHistory


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
# Group Serializers
# ============================================

class GroupRoleSerializer(serializers.Serializer):
    """Serializer for group role choices."""
    value = serializers.CharField()
    label = serializers.CharField()


class GroupMembershipSerializer(serializers.ModelSerializer):
    """
    Serializer for group membership.
    """
    user = UserSerializer(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = GroupMembership
        fields = [
            'id', 'user', 'role', 'role_display',
            'notifications_enabled', 'is_favorite', 'display_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GroupSerializer(serializers.ModelSerializer):
    """
    Serializer for Group model.
    """
    owner = UserSerializer(read_only=True)
    member_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Group
        fields = [
            'id', 'name', 'description', 'icon',
            'owner', 'is_private', 'is_active',
            'workspace_url', 'member_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner']


class GroupCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new group.
    """
    class Meta:
        model = Group
        fields = [
            'name', 'description', 'icon',
            'is_private', 'workspace_url'
        ]


class GroupUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a group.
    """
    class Meta:
        model = Group
        fields = [
            'name', 'description', 'icon',
            'is_private', 'workspace_url', 'is_active'
        ]


class GroupAddMemberSerializer(serializers.Serializer):
    """
    Serializer for adding a member to a group.
    """
    user_id = serializers.IntegerField()
    role = serializers.ChoiceField(
        choices=GroupRole.choices(),
        default=GroupRole.MEMBER.value
    )


class GroupMembershipUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating group membership.
    """
    role = serializers.ChoiceField(choices=GroupRole.choices())


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
    group = GroupSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    member_count = serializers.ReadOnlyField()
    channel_type_display = serializers.CharField(source='get_channel_type_display', read_only=True)
    
    class Meta:
        model = Channel
        fields = [
            'id', 'name', 'description', 'topic',
            'group', 'created_by', 'channel_type', 'channel_type_display',
            'is_active', 'is_archived', 'member_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'group', 'created_by']


class ChannelCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new channel.
    """
    group_id = serializers.IntegerField()
    
    class Meta:
        model = Channel
        fields = [
            'name', 'description', 'topic',
            'group_id', 'channel_type'
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
    group_id = serializers.IntegerField(help_text="ID of the group context")


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


class MessageDetailSerializer(MessageSerializer):
    """
    Detailed message serializer with edit history.
    """
    edit_history = MessageEditHistorySerializer(many=True, read_only=True)
    
    class Meta(MessageSerializer.Meta):
        fields = MessageSerializer.Meta.fields + ['edit_history']


class MessageThreadSerializer(MessageSerializer):
    """
    Serializer for message with thread replies.
    """
    replies = MessageSerializer(many=True, read_only=True)
    
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

