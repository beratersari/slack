"""
URL configuration for core API endpoints.
"""
from django.urls import path
from .views import (
    # User views
    UserTypesView, RegisterView, LoginView, LogoutView,
    TokenRefreshView, UserProfileView, ChangePasswordView,
    PasswordResetRequestView, PasswordResetConfirmView,
    UserListView, UserDetailView, UserSearchView, UserStatisticsView,
    # Workspace views
    WorkspaceListView, WorkspaceDetailView, WorkspaceMembersView,
    WorkspaceMemberDetailView, WorkspaceSearchView,
    # Channel views
    ChannelListView, ChannelDetailView, ChannelMembersView,
    ChannelMemberDetailView, ChannelJoinView, ChannelSearchView,
    DirectMessageView,
    # Channel Section views
    ChannelSectionListView, ChannelSectionDetailView, ChannelSectionReorderView,
    ChannelSectionToggleCollapseView, ChannelSectionChannelView,
    ChannelSectionReorderChannelsView, ChannelSectionMoveChannelView,
    # Message views
    ChannelMessagesView, MessageDetailView, MessageThreadView,
    MessageEditHistoryView, DirectMessageListView, DirectMessageConversationView,
    MessageSearchView,
    # Emoji views
    MessageReactionsView, MessageReactionToggleView,
    CustomEmojiListView, CustomEmojiDetailView, CustomEmojiAliasView, CustomEmojiSearchView,
    # Notification views
    NotificationListView, NotificationDetailView, NotificationSettingsView,
    UnreadCountView, ChannelUnreadView, KeywordAlertListView, KeywordAlertDetailView,
    MuteChannelView, DoNotDisturbView
)

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/password/change/', ChangePasswordView.as_view(), name='change-password'),
    path('auth/password/reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('auth/password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # User profile endpoints
    path('users/me/', UserProfileView.as_view(), name='user-profile'),
    path('users/search/', UserSearchView.as_view(), name='user-search'),
    path('users/statistics/', UserStatisticsView.as_view(), name='user-statistics'),
    path('users/types/', UserTypesView.as_view(), name='user-types'),
    
    # User management endpoints (admin only)
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:user_id>/', UserDetailView.as_view(), name='user-detail'),
    
    # Workspace endpoints
    path('workspaces/', WorkspaceListView.as_view(), name='workspace-list'),
    path('workspaces/search/', WorkspaceSearchView.as_view(), name='workspace-search'),
    path('workspaces/<int:workspace_id>/', WorkspaceDetailView.as_view(), name='workspace-detail'),
    path('workspaces/<int:workspace_id>/members/', WorkspaceMembersView.as_view(), name='workspace-members'),
    path('workspaces/<int:workspace_id>/members/<int:user_id>/', WorkspaceMemberDetailView.as_view(), name='workspace-member-detail'),
    
    # Channel endpoints
    path('channels/', ChannelListView.as_view(), name='channel-list'),
    path('channels/search/', ChannelSearchView.as_view(), name='channel-search'),
    path('channels/dm/', DirectMessageView.as_view(), name='direct-message'),
    path('channels/<int:channel_id>/', ChannelDetailView.as_view(), name='channel-detail'),
    path('channels/<int:channel_id>/join/', ChannelJoinView.as_view(), name='channel-join'),
    path('channels/<int:channel_id>/members/', ChannelMembersView.as_view(), name='channel-members'),
    path('channels/<int:channel_id>/members/<int:user_id>/', ChannelMemberDetailView.as_view(), name='channel-member-detail'),
    
    # Message endpoints
    path('channels/<int:channel_id>/messages/', ChannelMessagesView.as_view(), name='channel-messages'),
    path('messages/<int:message_id>/', MessageDetailView.as_view(), name='message-detail'),
    path('messages/<int:message_id>/thread/', MessageThreadView.as_view(), name='message-thread'),
    path('messages/<int:message_id>/history/', MessageEditHistoryView.as_view(), name='message-history'),
    path('messages/search/', MessageSearchView.as_view(), name='message-search'),
    
    # Direct Message endpoints
    path('dm/', DirectMessageListView.as_view(), name='dm-list'),
    path('dm/<int:user_id>/', DirectMessageConversationView.as_view(), name='dm-conversation'),

    # Channel Section endpoints
    path('sections/', ChannelSectionListView.as_view(), name='section-list'),
    path('sections/reorder/', ChannelSectionReorderView.as_view(), name='section-reorder'),
    path('sections/move-channel/', ChannelSectionMoveChannelView.as_view(), name='section-move-channel'),
    path('sections/<int:section_id>/', ChannelSectionDetailView.as_view(), name='section-detail'),
    path('sections/<int:section_id>/toggle-collapse/', ChannelSectionToggleCollapseView.as_view(), name='section-toggle-collapse'),
    path('sections/<int:section_id>/channels/', ChannelSectionChannelView.as_view(), name='section-channels'),
    path('sections/<int:section_id>/reorder-channels/', ChannelSectionReorderChannelsView.as_view(), name='section-reorder-channels'),

    # Emoji endpoints
    path('messages/<int:message_id>/reactions/', MessageReactionsView.as_view(), name='message-reactions'),
    path('messages/<int:message_id>/reactions/toggle/', MessageReactionToggleView.as_view(), name='message-reaction-toggle'),
    path('emojis/', CustomEmojiListView.as_view(), name='emoji-list'),
    path('emojis/search/', CustomEmojiSearchView.as_view(), name='emoji-search'),
    path('emojis/alias/', CustomEmojiAliasView.as_view(), name='emoji-alias'),
    path('emojis/<int:emoji_id>/', CustomEmojiDetailView.as_view(), name='emoji-detail'),

    # Notification endpoints
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:notification_id>/', NotificationDetailView.as_view(), name='notification-detail'),
    path('notifications/settings/', NotificationSettingsView.as_view(), name='notification-settings'),
    path('notifications/unread/', UnreadCountView.as_view(), name='unread-count'),
    path('notifications/unread/<int:channel_id>/', ChannelUnreadView.as_view(), name='channel-unread'),
    path('notifications/keywords/', KeywordAlertListView.as_view(), name='keyword-alert-list'),
    path('notifications/keywords/<int:keyword_id>/', KeywordAlertDetailView.as_view(), name='keyword-alert-detail'),
    path('notifications/mute/channel/<int:channel_id>/', MuteChannelView.as_view(), name='mute-channel'),
    path('notifications/dnd/', DoNotDisturbView.as_view(), name='do-not-disturb'),
]
