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
    # Group views
    GroupListView, GroupDetailView, GroupMembersView, 
    GroupMemberDetailView, GroupSearchView,
    # Channel views
    ChannelListView, ChannelDetailView, ChannelMembersView,
    ChannelMemberDetailView, ChannelJoinView, ChannelSearchView,
    DirectMessageView,
    # Message views
    ChannelMessagesView, MessageDetailView, MessageThreadView,
    MessageEditHistoryView, DirectMessageListView, DirectMessageConversationView,
    MessageSearchView
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
    
    # Group endpoints
    path('groups/', GroupListView.as_view(), name='group-list'),
    path('groups/search/', GroupSearchView.as_view(), name='group-search'),
    path('groups/<int:group_id>/', GroupDetailView.as_view(), name='group-detail'),
    path('groups/<int:group_id>/members/', GroupMembersView.as_view(), name='group-members'),
    path('groups/<int:group_id>/members/<int:user_id>/', GroupMemberDetailView.as_view(), name='group-member-detail'),
    
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
]
