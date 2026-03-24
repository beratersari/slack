"""
API Views for authentication and user management.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import logout as django_logout
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

from core.models import User, UserType, Workspace, WorkspaceRole, Channel, ChannelType, ChannelRole
from core.services import AuthService, UserService, WorkspaceService, ChannelService, ChannelSectionService, MessageService, EmojiService, NotificationService
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    LoginSerializer, LoginResponseSerializer, RegisterSerializer,
    ChangePasswordSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, TokenRefreshSerializer,
    UserTypeSerializer,
    # Workspace serializers
    WorkspaceSerializer, WorkspaceCreateSerializer, WorkspaceUpdateSerializer,
    WorkspaceMembershipSerializer, WorkspaceAddMemberSerializer, WorkspaceMembershipUpdateSerializer,
    # Channel serializers
    ChannelSerializer, ChannelListSerializer, ChannelDetailSerializer,
    ChannelCreateSerializer, ChannelUpdateSerializer,
    ChannelMembershipSerializer, ChannelMembershipListSerializer,
    ChannelAddMemberSerializer, DirectMessageSerializer,
    # Channel Section serializers
    ChannelSectionSerializer, ChannelSectionCreateSerializer, ChannelSectionUpdateSerializer,
    ChannelSectionReorderSerializer, AddChannelToSectionSerializer, ReorderChannelsSerializer, MoveChannelSerializer,
    # Message serializers
    MessageSerializer, MessageListSerializer, MessageDetailSerializer, MessageEditHistorySerializer,
    MessageCreateSerializer, MessageReplySerializer, MessageEditSerializer,
    DirectMessageCreateSerializer, DMConversationSerializer,
    # Emoji serializers
    MessageReactionSerializer, ReactionSummarySerializer, MessageReactionsResponseSerializer,
    AddReactionSerializer, CustomEmojiSerializer, CustomEmojiCreateSerializer, CustomEmojiAliasSerializer,
    # Notification serializers
    NotificationSerializer, NotificationListSerializer, NotificationSettingsSerializer,
    NotificationSettingsUpdateSerializer, UnreadCountSerializer, UnreadSummarySerializer,
    KeywordAlertSerializer, KeywordAlertCreateSerializer, MarkNotificationReadSerializer
)


class UserTypesView(APIView):
    """
    API view to get available user types.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Get user types",
        description="Returns list of available user types in the system",
        responses={200: UserTypeSerializer(many=True)}
    )
    def get(self, request):
        """Get all available user types."""
        user_types = [{'value': t.value, 'label': t.name.replace('_', ' ').title()} 
                      for t in UserType]
        return Response(user_types)


class RegisterView(APIView):
    """
    API view for user registration.
    """
    permission_classes = [AllowAny]
    
    def __init__(self):
        super().__init__()
        self.auth_service = AuthService()
    
    @extend_schema(
        summary="Register new user",
        request=RegisterSerializer,
        responses={201: OpenApiExample('Success', value={'message': 'User registered successfully', 'user': {}, 'token': 'jwt-token'})}
    )
    def post(self, request):
        """Register a new user."""
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = self.auth_service.register_user(
                email=serializer.validated_data['email'],
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password'],
                first_name=serializer.validated_data.get('first_name', ''),
                last_name=serializer.validated_data.get('last_name', ''),
            )
            
            # Generate token
            token = self.auth_service.generate_jwt_token(user)
            
            return Response({
                'message': 'User registered successfully',
                'user': UserSerializer(user).data,
                'token': token
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    API view for user login.
    """
    permission_classes = [AllowAny]
    
    def __init__(self):
        super().__init__()
        self.auth_service = AuthService()
    
    @extend_schema(
        summary="User login",
        request=LoginSerializer,
        responses={200: OpenApiExample('Success', value={'message': 'Login successful', 'user': {}, 'token': 'jwt-token'})}
    )
    def post(self, request):
        """Authenticate user and return JWT token."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = self.auth_service.verify_credentials(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )
        
        if user:
            # Generate JWT token (no session - API uses stateless JWT auth)
            token = self.auth_service.generate_jwt_token(user)
            
            return Response({
                'message': 'Login successful',
                'user': UserSerializer(user).data,
                'token': token
            })
        
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )


class LogoutView(APIView):
    """
    API view for user logout.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(summary="User logout")
    def post(self, request):
        """Logout user and invalidate session."""
        self.auth_service = AuthService()
        self.auth_service.logout(request)
        return Response({'message': 'Logged out successfully'})


class TokenRefreshView(APIView):
    """
    API view for refreshing JWT token.
    """
    permission_classes = [AllowAny]
    
    def __init__(self):
        super().__init__()
        self.auth_service = AuthService()
    
    @extend_schema(
        summary="Refresh JWT token",
        request=TokenRefreshSerializer,
        responses={200: OpenApiExample('Success', value={'token': 'new-jwt-token'})}
    )
    def post(self, request):
        """Refresh JWT token."""
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_token = self.auth_service.refresh_token(
            serializer.validated_data['token']
        )
        
        if new_token:
            return Response({'token': new_token})
        
        return Response(
            {'error': 'Invalid or expired token'},
            status=status.HTTP_401_UNAUTHORIZED
        )


class UserProfileView(APIView):
    """
    API view for user profile operations.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.user_service = UserService()
    
    @extend_schema(summary="Get current user profile", responses={200: UserSerializer})
    def get(self, request):
        """Get current user profile."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    @extend_schema(summary="Update current user profile", request=UserUpdateSerializer)
    def patch(self, request):
        """Update current user profile."""
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Profile updated successfully',
            'user': UserSerializer(request.user).data
        })


class ChangePasswordView(APIView):
    """
    API view for changing password.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.auth_service = AuthService()
    
    @extend_schema(summary="Change password", request=ChangePasswordSerializer)
    def post(self, request):
        """Change user password."""
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            self.auth_service.change_password(
                user_id=request.user.id,
                old_password=serializer.validated_data['old_password'],
                new_password=serializer.validated_data['new_password']
            )
            return Response({'message': 'Password changed successfully'})
            
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    """
    API view for requesting password reset.
    """
    permission_classes = [AllowAny]
    
    def __init__(self):
        super().__init__()
        self.auth_service = AuthService()
    
    @extend_schema(summary="Request password reset", request=PasswordResetRequestSerializer)
    def post(self, request):
        """Request password reset token."""
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = self.auth_service.request_password_reset(
            serializer.validated_data['email']
        )
        
        # Always return success to prevent email enumeration
        return Response({
            'message': 'If the email exists, a password reset link has been sent'
        })


class PasswordResetConfirmView(APIView):
    """
    API view for confirming password reset.
    """
    permission_classes = [AllowAny]
    
    def __init__(self):
        super().__init__()
        self.auth_service = AuthService()
    
    @extend_schema(summary="Confirm password reset", request=PasswordResetConfirmSerializer)
    def post(self, request):
        """Reset password using token."""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            self.auth_service.reset_password(
                token=serializer.validated_data['token'],
                new_password=serializer.validated_data['new_password']
            )
            return Response({'message': 'Password reset successfully'})
            
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserListView(APIView):
    """
    API view for listing and creating users (admin only).
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.user_service = UserService()
    
    @extend_schema(summary="List all users (admin only)", responses={200: UserSerializer(many=True)})
    def get(self, request):
        """Get list of users (admin only)."""
        if not request.user.is_admin():
            return Response(
                {'error': 'Only admins can view user list'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        users = self.user_service.get_active_users()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
    @extend_schema(summary="Create new user (admin only)", request=UserCreateSerializer)
    def post(self, request):
        """Create a new user (admin only)."""
        if not request.user.is_admin():
            return Response(
                {'error': 'Only admins can create users'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = self.user_service.create_user(
                email=serializer.validated_data['email'],
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password'],
                first_name=serializer.validated_data.get('first_name', ''),
                last_name=serializer.validated_data.get('last_name', ''),
                user_type=serializer.validated_data.get('user_type', UserType.USER.value),
            )
            
            return Response({
                'message': 'User created successfully',
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(APIView):
    """
    API view for individual user operations (admin only).
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.user_service = UserService()
    
    @extend_schema(summary="Get user by ID (admin only)", responses={200: UserSerializer})
    def get(self, request, user_id):
        """Get user by ID (admin only)."""
        if not request.user.is_admin():
            return Response(
                {'error': 'Only admins can view user details'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.user_service.get_user_by_id(user_id)
        if not user:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = UserSerializer(user)
        return Response(serializer.data)
    
    @extend_schema(summary="Update user by ID (admin only)", request=UserUpdateSerializer)
    def patch(self, request, user_id):
        """Update user by ID (admin only)."""
        if not request.user.is_admin():
            return Response(
                {'error': 'Only admins can update users'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            user = self.user_service.update_user(user_id, **request.data)
            if user:
                return Response({
                    'message': 'User updated successfully',
                    'user': UserSerializer(user).data
                })
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(summary="Delete user by ID (admin only)")
    def delete(self, request, user_id):
        """Delete user by ID (admin only)."""
        if not request.user.is_admin():
            return Response(
                {'error': 'Only admins can delete users'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            self.user_service.delete_user(user_id)
            return Response({'message': 'User deleted successfully'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)


class UserSearchView(APIView):
    """
    API view for searching users.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.user_service = UserService()
    
    @extend_schema(
        summary="Search users",
        parameters=[OpenApiParameter(name='q', description='Search query', required=True, type=str)],
        responses={200: UserSerializer(many=True)}
    )
    def get(self, request):
        """Search users by query."""
        query = request.query_params.get('q', '')
        users = self.user_service.search_users(query)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


class UserStatisticsView(APIView):
    """
    API view for user statistics (admin only).
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.user_service = UserService()
    
    @extend_schema(summary="Get user statistics (admin only)")
    def get(self, request):
        """Get user statistics."""
        if not request.user.is_admin():
            return Response(
                {'error': 'Only admins can view statistics'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        stats = self.user_service.get_user_statistics()
        return Response(stats)


# ============================================
# Workspace Views
# ============================================

class WorkspaceListView(APIView):
    """
    API view for listing and creating workspaces.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.workspace_service = WorkspaceService()
    
    @extend_schema(
        summary="List workspaces",
        description="Returns workspaces the user is a member of (or all workspaces for admins)",
        responses={200: WorkspaceSerializer(many=True)}
    )
    def get(self, request):
        """Get list of workspaces."""
        if request.user.is_admin() or request.user.is_super_user_type():
            workspaces = self.workspace_service.get_active_workspaces()
        else:
            workspaces = self.workspace_service.get_workspaces_by_member(request.user.id)
        
        serializer = WorkspaceSerializer(workspaces, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Create workspace",
        description="Create a new workspace (admin/super user only)",
        request=WorkspaceCreateSerializer,
        responses={201: WorkspaceSerializer}
    )
    def post(self, request):
        """Create a new workspace."""
        serializer = WorkspaceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            workspace = self.workspace_service.create_workspace(
                name=serializer.validated_data['name'],
                owner_id=request.user.id,
                description=serializer.validated_data.get('description', ''),
                is_private=serializer.validated_data.get('is_private', False),
                icon=serializer.validated_data.get('icon'),
                workspace_url=serializer.validated_data.get('workspace_url'),
            )
            
            return Response({
                'message': 'Workspace created successfully',
                'workspace': WorkspaceSerializer(workspace).data
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class WorkspaceDetailView(APIView):
    """
    API view for individual workspace operations.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.workspace_service = WorkspaceService()
    
    @extend_schema(summary="Get workspace by ID", responses={200: WorkspaceSerializer})
    def get(self, request, workspace_id):
        """Get workspace by ID."""
        workspace = self.workspace_service.get_workspace_by_id(workspace_id)
        if not workspace:
            return Response({'error': 'Workspace not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check access
        if workspace.is_private and not self.workspace_service.is_member(workspace_id, request.user.id):
            if not (request.user.is_admin() or request.user.is_super_user_type()):
                return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = WorkspaceSerializer(workspace)
        return Response(serializer.data)
    
    @extend_schema(summary="Update workspace", request=WorkspaceUpdateSerializer)
    def patch(self, request, workspace_id):
        """Update workspace."""
        serializer = WorkspaceUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            workspace = self.workspace_service.update_workspace(
                workspace_id=workspace_id,
                user_id=request.user.id,
                **serializer.validated_data
            )
            return Response({
                'message': 'Workspace updated successfully',
                'workspace': WorkspaceSerializer(workspace).data
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(summary="Delete workspace")
    def delete(self, request, workspace_id):
        """Delete workspace."""
        try:
            self.workspace_service.delete_workspace(workspace_id, request.user.id)
            return Response({'message': 'Workspace deleted successfully'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class WorkspaceMembersView(APIView):
    """
    API view for workspace membership operations.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.workspace_service = WorkspaceService()
    
    @extend_schema(summary="Get workspace members", responses={200: WorkspaceMembershipSerializer(many=True)})
    def get(self, request, workspace_id):
        """Get all members of a workspace."""
        members = self.workspace_service.get_workspace_members(workspace_id)
        serializer = WorkspaceMembershipSerializer(members, many=True)
        return Response(serializer.data)
    
    @extend_schema(summary="Add member to workspace", request=WorkspaceAddMemberSerializer)
    def post(self, request, workspace_id):
        """Add a member to a workspace."""
        serializer = WorkspaceAddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            membership = self.workspace_service.add_member(
                workspace_id=workspace_id,
                user_id=serializer.validated_data['user_id'],
                added_by_id=request.user.id,
                role=serializer.validated_data.get('role', WorkspaceRole.MEMBER.value)
            )
            return Response({
                'message': 'Member added successfully',
                'membership': WorkspaceMembershipSerializer(membership).data
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class WorkspaceMemberDetailView(APIView):
    """
    API view for individual workspace member operations.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.workspace_service = WorkspaceService()
    
    @extend_schema(summary="Update member role", request=WorkspaceMembershipUpdateSerializer)
    def patch(self, request, workspace_id, user_id):
        """Update a member's role."""
        serializer = WorkspaceMembershipUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            membership = self.workspace_service.update_member_role(
                workspace_id=workspace_id,
                user_id=user_id,
                new_role=serializer.validated_data['role'],
                updated_by_id=request.user.id
            )
            return Response({
                'message': 'Member role updated',
                'membership': WorkspaceMembershipSerializer(membership).data
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(summary="Remove member from workspace")
    def delete(self, request, workspace_id, user_id):
        """Remove a member from a workspace."""
        try:
            self.workspace_service.remove_member(
                workspace_id=workspace_id,
                user_id=user_id,
                removed_by_id=request.user.id
            )
            return Response({'message': 'Member removed successfully'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class WorkspaceSearchView(APIView):
    """
    API view for searching workspaces.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.workspace_service = WorkspaceService()
    
    @extend_schema(
        summary="Search workspaces",
        parameters=[OpenApiParameter(name='q', description='Search query', required=True, type=str)],
        responses={200: WorkspaceSerializer(many=True)}
    )
    def get(self, request):
        """Search workspaces by query."""
        query = request.query_params.get('q', '')
        workspaces = self.workspace_service.search_workspaces(query, request.user.id)
        serializer = WorkspaceSerializer(workspaces, many=True)
        return Response(serializer.data)


# ============================================
# Channel Views
# ============================================

class ChannelListView(APIView):
    """
    API view for listing and creating channels.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.channel_service = ChannelService()
    
    @extend_schema(
        summary="List channels",
        parameters=[OpenApiParameter(name='workspace_id', description='Filter by workspace ID', required=False, type=int)],
        responses={200: ChannelListSerializer(many=True)}
    )
    def get(self, request):
        """Get list of channels."""
        workspace_id = request.query_params.get('workspace_id')
        
        if request.user.is_admin() or request.user.is_super_user_type():
            if workspace_id:
                channels = self.channel_service.get_channels_by_workspace(int(workspace_id))
            else:
                channels = self.channel_service.get_active_channels()
        else:
            channels = self.channel_service.get_channels_by_member(request.user.id)
            if workspace_id:
                channels = [c for c in channels if c.workspace_id == int(workspace_id)]
        
        serializer = ChannelListSerializer(channels, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Create channel",
        description="Create a new channel (admin/super user/workspace admin only)",
        request=ChannelCreateSerializer,
        responses={201: ChannelDetailSerializer}
    )
    def post(self, request):
        """Create a new channel."""
        serializer = ChannelCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            channel = self.channel_service.create_channel(
                name=serializer.validated_data['name'],
                workspace_id=serializer.validated_data['workspace_id'],
                created_by_id=request.user.id,
                channel_type=serializer.validated_data.get('channel_type', ChannelType.PUBLIC.value),
                description=serializer.validated_data.get('description', ''),
                topic=serializer.validated_data.get('topic', ''),
            )
            
            return Response({
                'message': 'Channel created successfully',
                'channel': ChannelDetailSerializer(channel).data
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChannelDetailView(APIView):
    """
    API view for individual channel operations.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.channel_service = ChannelService()
    
    @extend_schema(summary="Get channel by ID", responses={200: ChannelDetailSerializer})
    def get(self, request, channel_id):
        """Get channel by ID."""
        channel = self.channel_service.get_channel_by_id(channel_id)
        if not channel:
            return Response({'error': 'Channel not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check access for private channels
        if channel.is_private() and not self.channel_service.is_member(channel_id, request.user.id):
            if not (request.user.is_admin() or request.user.is_super_user_type()):
                return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ChannelDetailSerializer(channel)
        return Response(serializer.data)
    
    @extend_schema(summary="Update channel", request=ChannelUpdateSerializer)
    def patch(self, request, channel_id):
        """Update channel."""
        serializer = ChannelUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            channel = self.channel_service.update_channel(
                channel_id=channel_id,
                user_id=request.user.id,
                **serializer.validated_data
            )
            return Response({
                'message': 'Channel updated successfully',
                'channel': ChannelDetailSerializer(channel).data
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(summary="Delete channel")
    def delete(self, request, channel_id):
        """Delete channel."""
        try:
            self.channel_service.delete_channel(channel_id, request.user.id)
            return Response({'message': 'Channel deleted successfully'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChannelMembersView(APIView):
    """
    API view for channel membership operations.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.channel_service = ChannelService()
    
    @extend_schema(summary="Get channel members", responses={200: ChannelMembershipListSerializer(many=True)})
    def get(self, request, channel_id):
        """Get all members of a channel."""
        members = self.channel_service.get_channel_members(channel_id)
        serializer = ChannelMembershipListSerializer(members, many=True)
        return Response(serializer.data)
    
    @extend_schema(summary="Add member to channel", request=ChannelAddMemberSerializer)
    def post(self, request, channel_id):
        """Add a member to a channel."""
        serializer = ChannelAddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            membership = self.channel_service.add_member(
                channel_id=channel_id,
                user_id=serializer.validated_data['user_id'],
                added_by_id=request.user.id,
                role=serializer.validated_data.get('role', ChannelRole.MEMBER.value)
            )
            return Response({
                'message': 'Member added successfully',
                'membership': ChannelMembershipSerializer(membership).data
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChannelMemberDetailView(APIView):
    """
    API view for individual channel member operations.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.channel_service = ChannelService()
    
    @extend_schema(summary="Remove member from channel")
    def delete(self, request, channel_id, user_id):
        """Remove a member from a channel."""
        try:
            self.channel_service.remove_member(
                channel_id=channel_id,
                user_id=user_id,
                removed_by_id=request.user.id
            )
            return Response({'message': 'Member removed successfully'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChannelJoinView(APIView):
    """
    API view for joining a public channel.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.channel_service = ChannelService()
    
    @extend_schema(summary="Join a public channel", responses={201: ChannelMembershipListSerializer})
    def post(self, request, channel_id):
        """Join a public channel."""
        try:
            membership = self.channel_service.join_public_channel(channel_id, request.user.id)
            return Response({
                'message': 'Joined channel successfully',
                'membership': ChannelMembershipListSerializer(membership).data
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChannelSearchView(APIView):
    """
    API view for searching channels.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.channel_service = ChannelService()
    
    @extend_schema(
        summary="Search channels",
        parameters=[
            OpenApiParameter(name='q', description='Search query', required=True, type=str),
            OpenApiParameter(name='workspace_id', description='Filter by workspace ID', required=False, type=int)
        ],
        responses={200: ChannelListSerializer(many=True)}
    )
    def get(self, request):
        """Search channels by query."""
        query = request.query_params.get('q', '')
        workspace_id = request.query_params.get('workspace_id')
        
        channels = self.channel_service.search_channels(
            query=query,
            workspace_id=int(workspace_id) if workspace_id else None,
            user_id=request.user.id
        )
        serializer = ChannelListSerializer(channels, many=True)
        return Response(serializer.data)


class DirectMessageView(APIView):
    """
    API view for direct messages.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.channel_service = ChannelService()
    
    @extend_schema(
        summary="Get or create direct message channel",
        request=DirectMessageSerializer,
        responses={200: ChannelDetailSerializer}
    )
    def post(self, request):
        """Get or create a direct message channel."""
        serializer = DirectMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            channel = self.channel_service.get_or_create_dm_channel(
                user1_id=request.user.id,
                user2_id=serializer.validated_data['user_id'],
                workspace_id=serializer.validated_data['workspace_id']
            )
            return Response({
                'message': 'Direct message channel ready',
                'channel': ChannelDetailSerializer(channel).data
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ============================================
# Message Views
# ============================================

class ChannelMessagesView(APIView):
    """
    API view for channel messages.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.message_service = MessageService()
    
    @extend_schema(
        summary="Get channel messages",
        responses={200: MessageListSerializer(many=True)}
    )
    def get(self, request, channel_id):
        """Get all messages in a channel (top-level, not replies)."""
        try:
            messages = self.message_service.get_channel_messages(channel_id, request.user)
            serializer = MessageListSerializer(messages, many=True)
            return Response(serializer.data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="Send a message to a channel",
        request=MessageCreateSerializer,
        responses={201: MessageSerializer}
    )
    def post(self, request, channel_id):
        """Send a message to a channel."""
        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            message = self.message_service.send_channel_message(
                sender=request.user,
                channel_id=channel_id,
                content=serializer.validated_data['content']
            )
            return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MessageDetailView(APIView):
    """
    API view for single message operations.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.message_service = MessageService()
    
    @extend_schema(
        summary="Get message details with edit history",
        responses={200: MessageDetailSerializer}
    )
    def get(self, request, message_id):
        """Get a single message with edit history."""
        try:
            message = self.message_service.get_message(message_id, request.user)
            serializer = MessageDetailSerializer(message)
            return Response(serializer.data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
    
    @extend_schema(
        summary="Edit a message",
        request=MessageEditSerializer,
        responses={200: MessageSerializer}
    )
    def patch(self, request, message_id):
        """Edit a message (owner or admin only)."""
        serializer = MessageEditSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            message = self.message_service.edit_message(
                message_id=message_id,
                new_content=serializer.validated_data['content'],
                edited_by=request.user
            )
            return Response(MessageSerializer(message).data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="Delete a message",
        responses={200: OpenApiExample('Success', value={'message': 'Message deleted'})}
    )
    def delete(self, request, message_id):
        """Soft delete a message (owner or admin only)."""
        try:
            self.message_service.delete_message(message_id, request.user)
            return Response({'message': 'Message deleted'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MessageThreadView(APIView):
    """
    API view for message threads (replies).
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.message_service = MessageService()
    
    @extend_schema(
        summary="Get thread replies",
        responses={200: MessageListSerializer(many=True)}
    )
    def get(self, request, message_id):
        """Get all replies in a thread."""
        try:
            replies = self.message_service.get_thread_replies(message_id, request.user)
            serializer = MessageListSerializer(replies, many=True)
            return Response(serializer.data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="Reply to a message (create thread)",
        request=MessageReplySerializer,
        responses={201: MessageSerializer}
    )
    def post(self, request, message_id):
        """Reply to a message to create/start a thread."""
        serializer = MessageReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            reply = self.message_service.reply_to_message(
                sender=request.user,
                parent_message_id=message_id,
                content=serializer.validated_data['content']
            )
            return Response(MessageSerializer(reply).data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MessageEditHistoryView(APIView):
    """
    API view for viewing message edit history.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.message_service = MessageService()
    
    @extend_schema(
        summary="Get message edit history",
        responses={200: MessageEditHistorySerializer(many=True)}
    )
    def get(self, request, message_id):
        """Get the edit history of a message."""
        try:
            history = self.message_service.get_edit_history(message_id, request.user)
            serializer = MessageEditHistorySerializer(history, many=True)
            return Response(serializer.data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DirectMessageListView(APIView):
    """
    API view for listing DM conversations.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.message_service = MessageService()
    
    @extend_schema(
        summary="Get list of DM conversations",
        responses={200: DMConversationSerializer(many=True)}
    )
    def get(self, request):
        """Get list of all DM conversations for current user."""
        conversations = self.message_service.get_dm_conversations_list(request.user)
        serializer = DMConversationSerializer(conversations, many=True)
        return Response(serializer.data)


class DirectMessageConversationView(APIView):
    """
    API view for DM conversation with a specific user.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.message_service = MessageService()
    
    @extend_schema(
        summary="Get DM conversation with a user",
        responses={200: MessageListSerializer(many=True)}
    )
    def get(self, request, user_id):
        """Get DM conversation with a specific user."""
        try:
            messages = self.message_service.get_dm_conversation(request.user, user_id)
            serializer = MessageListSerializer(messages, many=True)
            return Response(serializer.data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="Send a direct message",
        request=DirectMessageCreateSerializer,
        responses={201: MessageSerializer}
    )
    def post(self, request, user_id):
        """Send a direct message to a user."""
        serializer = DirectMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            message = self.message_service.send_direct_message(
                sender=request.user,
                recipient_id=user_id,
                content=serializer.validated_data['content']
            )
            return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MessageSearchView(APIView):
    """
    API view for searching messages.
    """
    permission_classes = [IsAuthenticated]

    def __init__(self):
        super().__init__()
        self.message_service = MessageService()

    @extend_schema(
        summary="Search messages",
        parameters=[
            OpenApiParameter(name='q', description='Search query', required=True, type=str),
            OpenApiParameter(name='channel_id', description='Filter by channel ID', required=False, type=int),
        ],
        responses={200: MessageListSerializer(many=True)}
    )
    def get(self, request):
        """Search messages by content."""
        query = request.query_params.get('q', '')
        channel_id = request.query_params.get('channel_id')

        messages = self.message_service.search_messages(
            query=query,
            user=request.user,
            channel_id=int(channel_id) if channel_id else None
        )
        serializer = MessageListSerializer(messages, many=True)
        return Response(serializer.data)


# ============================================
# Channel Section Views
# ============================================

class ChannelSectionListView(APIView):
    """
    API view for listing and creating channel sections.
    """
    permission_classes = [IsAuthenticated]

    def __init__(self):
        super().__init__()
        self.section_service = ChannelSectionService()

    @extend_schema(
        summary="List channel sections",
        description="Returns all channel sections for the user in the specified workspace",
        parameters=[
            OpenApiParameter(name='workspace_id', description='Workspace ID', required=True, type=int),
        ],
        responses={200: ChannelSectionSerializer(many=True)}
    )
    def get(self, request):
        """Get all channel sections for the user in a workspace."""
        workspace_id = request.query_params.get('workspace_id')
        if not workspace_id:
            return Response(
                {'error': 'workspace_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        sections = self.section_service.get_user_sections(
            user_id=request.user.id,
            workspace_id=int(workspace_id)
        )
        serializer = ChannelSectionSerializer(sections, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Create channel section",
        description="Create a new custom channel section",
        request=ChannelSectionCreateSerializer,
        responses={201: ChannelSectionSerializer}
    )
    def post(self, request):
        """Create a new custom channel section."""
        workspace_id = request.query_params.get('workspace_id')
        if not workspace_id:
            return Response(
                {'error': 'workspace_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ChannelSectionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            section = self.section_service.create_custom_section(
                name=serializer.validated_data['name'],
                user_id=request.user.id,
                workspace_id=int(workspace_id),
                color=serializer.validated_data.get('color'),
                order=serializer.validated_data.get('order', 0)
            )
            return Response({
                'message': 'Section created successfully',
                'section': ChannelSectionSerializer(section).data
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChannelSectionDetailView(APIView):
    """
    API view for individual channel section operations.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ChannelSectionSerializer

    def __init__(self):
        super().__init__()
        self.section_service = ChannelSectionService()

    @extend_schema(
        summary="Get channel section",
        responses={200: ChannelSectionSerializer}
    )
    def get(self, request, section_id):
        """Get a channel section with its channels."""
        try:
            result = self.section_service.get_section_with_channels(
                section_id=section_id,
                user_id=request.user.id
            )
            if not result:
                return Response(
                    {'error': 'Section not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            serializer = ChannelSectionSerializer(result['section'])
            return Response(serializer.data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)

    @extend_schema(
        summary="Update channel section",
        request=ChannelSectionUpdateSerializer,
        responses={200: ChannelSectionSerializer}
    )
    def patch(self, request, section_id):
        """Update a channel section."""
        serializer = ChannelSectionUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            section = self.section_service.update_section(
                section_id=section_id,
                user_id=request.user.id,
                **serializer.validated_data
            )
            return Response({
                'message': 'Section updated successfully',
                'section': ChannelSectionSerializer(section).data
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(summary="Delete channel section")
    def delete(self, request, section_id):
        """Delete a custom channel section."""
        try:
            self.section_service.delete_section(section_id, request.user.id)
            return Response({'message': 'Section deleted successfully'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChannelSectionReorderView(APIView):
    """
    API view for reordering channel sections.
    """
    permission_classes = [IsAuthenticated]

    def __init__(self):
        super().__init__()
        self.section_service = ChannelSectionService()

    @extend_schema(
        summary="Reorder sections",
        request=ChannelSectionReorderSerializer,
        responses={200: ChannelSectionSerializer(many=True)}
    )
    def post(self, request):
        """Reorder channel sections."""
        workspace_id = request.query_params.get('workspace_id')
        if not workspace_id:
            return Response(
                {'error': 'workspace_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ChannelSectionReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            sections = self.section_service.reorder_sections(
                user_id=request.user.id,
                workspace_id=int(workspace_id),
                section_orders=serializer.validated_data['section_orders']
            )
            return Response({
                'message': 'Sections reordered successfully',
                'sections': ChannelSectionSerializer(sections, many=True).data
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChannelSectionToggleCollapseView(APIView):
    """
    API view for toggling section collapsed state.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ChannelSectionSerializer

    def __init__(self):
        super().__init__()
        self.section_service = ChannelSectionService()

    @extend_schema(
        summary="Toggle section collapsed",
        responses={200: ChannelSectionSerializer}
    )
    def post(self, request, section_id):
        """Toggle the collapsed state of a section."""
        try:
            section = self.section_service.toggle_section_collapsed(
                section_id=section_id,
                user_id=request.user.id
            )
            return Response({
                'message': 'Section collapsed state toggled',
                'section': ChannelSectionSerializer(section).data
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChannelSectionChannelView(APIView):
    """
    API view for managing channels within a section.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ChannelSectionSerializer

    def __init__(self):
        super().__init__()
        self.section_service = ChannelSectionService()

    @extend_schema(
        summary="Add channel to section",
        request=AddChannelToSectionSerializer,
        responses={201: ChannelSectionSerializer}
    )
    def post(self, request, section_id):
        """Add a channel to a section."""
        serializer = AddChannelToSectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            self.section_service.add_channel_to_section(
                section_id=section_id,
                channel_id=serializer.validated_data['channel_id'],
                user_id=request.user.id,
                order=serializer.validated_data.get('order', 0)
            )
            # Return updated section
            result = self.section_service.get_section_with_channels(section_id, request.user.id)
            return Response({
                'message': 'Channel added to section',
                'section': ChannelSectionSerializer(result['section']).data
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Remove channel from section",
        parameters=[
            OpenApiParameter(name='channel_id', description='Channel ID to remove', required=True, type=int),
        ]
    )
    def delete(self, request, section_id):
        """Remove a channel from a section."""
        channel_id = request.query_params.get('channel_id')
        if not channel_id:
            return Response(
                {'error': 'channel_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            self.section_service.remove_channel_from_section(
                section_id=section_id,
                channel_id=int(channel_id),
                user_id=request.user.id
            )
            return Response({'message': 'Channel removed from section'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChannelSectionReorderChannelsView(APIView):
    """
    API view for reordering channels within a section.
    """
    permission_classes = [IsAuthenticated]

    def __init__(self):
        super().__init__()
        self.section_service = ChannelSectionService()

    @extend_schema(
        summary="Reorder channels in section",
        request=ReorderChannelsSerializer,
        responses={200: ChannelSectionSerializer}
    )
    def post(self, request, section_id):
        """Reorder channels within a section."""
        serializer = ReorderChannelsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            self.section_service.reorder_channels_in_section(
                section_id=section_id,
                user_id=request.user.id,
                item_orders=serializer.validated_data['item_orders']
            )
            # Return updated section
            result = self.section_service.get_section_with_channels(section_id, request.user.id)
            return Response({
                'message': 'Channels reordered successfully',
                'section': ChannelSectionSerializer(result['section']).data
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChannelSectionMoveChannelView(APIView):
    """
    API view for moving a channel from one section to another.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MoveChannelSerializer

    def __init__(self):
        super().__init__()
        self.section_service = ChannelSectionService()

    @extend_schema(
        summary="Move channel to another section",
        request=MoveChannelSerializer
    )
    def post(self, request):
        """Move a channel from one section to another."""
        serializer = MoveChannelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            self.section_service.move_channel_to_section(
                channel_id=serializer.validated_data.get('channel_id'),
                from_section_id=serializer.validated_data.get('from_section_id'),
                to_section_id=serializer.validated_data.get('to_section_id'),
                user_id=request.user.id,
                order=serializer.validated_data.get('order', 0)
            )
            return Response({'message': 'Channel moved successfully'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ============================================
# Emoji Views
# ============================================

class MessageReactionsView(APIView):
    """
    API view for message reactions (👍, ❤️, 😂 etc.).
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MessageReactionsResponseSerializer

    def __init__(self):
        super().__init__()
        self.emoji_service = EmojiService()

    @extend_schema(
        summary="Get message reactions",
        description="Returns all reactions for a message with count summary",
        responses={200: MessageReactionsResponseSerializer}
    )
    def get(self, request, message_id):
        """Get all reactions for a message."""
        try:
            reactions_data = self.emoji_service.get_message_reactions(message_id)
            return Response(reactions_data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        summary="Add reaction to message",
        request=AddReactionSerializer,
        responses={201: MessageReactionSerializer}
    )
    def post(self, request, message_id):
        """Add a reaction to a message."""
        serializer = AddReactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            reaction = self.emoji_service.add_reaction(
                message_id=message_id,
                user_id=request.user.id,
                emoji=serializer.validated_data['emoji']
            )
            return Response({
                'message': 'Reaction added',
                'reaction': MessageReactionSerializer(reaction).data
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Remove reaction from message",
        parameters=[
            OpenApiParameter(name='emoji', description='Emoji to remove', required=True, type=str),
        ]
    )
    def delete(self, request, message_id):
        """Remove a reaction from a message."""
        emoji = request.query_params.get('emoji')
        if not emoji:
            return Response(
                {'error': 'emoji parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            self.emoji_service.remove_reaction(
                message_id=message_id,
                user_id=request.user.id,
                emoji=emoji
            )
            return Response({'message': 'Reaction removed'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MessageReactionToggleView(APIView):
    """
    API view for toggling reactions on/off.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AddReactionSerializer

    def __init__(self):
        super().__init__()
        self.emoji_service = EmojiService()

    @extend_schema(
        summary="Toggle reaction",
        description="Add reaction if not present, remove if already exists",
        request=AddReactionSerializer,
        responses={200: MessageReactionSerializer}
    )
    def post(self, request, message_id):
        """Toggle a reaction on a message."""
        serializer = AddReactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = self.emoji_service.toggle_reaction(
                message_id=message_id,
                user_id=request.user.id,
                emoji=serializer.validated_data['emoji']
            )
            return Response({
                'action': result['action'],
                'reaction': MessageReactionSerializer(result['reaction']).data if result['reaction'] else None
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CustomEmojiListView(APIView):
    """
    API view for listing and creating custom emojis.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CustomEmojiSerializer

    def __init__(self):
        super().__init__()
        self.emoji_service = EmojiService()

    @extend_schema(
        summary="List custom emojis",
        description="Returns all custom emojis for a workspace",
        parameters=[
            OpenApiParameter(name='workspace_id', description='Workspace ID', required=True, type=int),
        ],
        responses={200: CustomEmojiSerializer(many=True)}
    )
    def get(self, request):
        """Get all custom emojis for a workspace."""
        workspace_id = request.query_params.get('workspace_id')
        if not workspace_id:
            return Response(
                {'error': 'workspace_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        emojis = self.emoji_service.get_workspace_emojis(int(workspace_id))
        serializer = CustomEmojiSerializer(emojis, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Create custom emoji",
        description="Upload a new custom emoji (admin only)",
        request=CustomEmojiCreateSerializer,
        responses={201: CustomEmojiSerializer}
    )
    def post(self, request):
        """Create a new custom emoji."""
        workspace_id = request.query_params.get('workspace_id')
        if not workspace_id:
            return Response(
                {'error': 'workspace_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CustomEmojiCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            emoji = self.emoji_service.create_custom_emoji(
                name=serializer.validated_data['name'],
                image=serializer.validated_data['image'],
                workspace_id=int(workspace_id),
                created_by_id=request.user.id
            )
            return Response({
                'message': 'Custom emoji created',
                'emoji': CustomEmojiSerializer(emoji).data
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CustomEmojiDetailView(APIView):
    """
    API view for individual custom emoji operations.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CustomEmojiSerializer

    def __init__(self):
        super().__init__()
        self.emoji_service = EmojiService()

    @extend_schema(
        summary="Get custom emoji",
        responses={200: CustomEmojiSerializer}
    )
    def get(self, request, emoji_id):
        """Get a custom emoji by ID."""
        emoji = self.emoji_service.emoji_repository.get_by_id(emoji_id)
        if not emoji:
            return Response(
                {'error': 'Emoji not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = CustomEmojiSerializer(emoji)
        return Response(serializer.data)

    @extend_schema(summary="Delete custom emoji")
    def delete(self, request, emoji_id):
        """Delete a custom emoji."""
        try:
            self.emoji_service.delete_custom_emoji(emoji_id, request.user.id)
            return Response({'message': 'Emoji deleted successfully'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)


class CustomEmojiAliasView(APIView):
    """
    API view for creating emoji aliases.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CustomEmojiAliasSerializer

    def __init__(self):
        super().__init__()
        self.emoji_service = EmojiService()

    @extend_schema(
        summary="Create emoji alias",
        description="Create an alternative name for an existing emoji",
        request=CustomEmojiAliasSerializer,
        responses={201: CustomEmojiSerializer}
    )
    def post(self, request):
        """Create an alias for an existing emoji."""
        workspace_id = request.query_params.get('workspace_id')
        if not workspace_id:
            return Response(
                {'error': 'workspace_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CustomEmojiAliasSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            alias = self.emoji_service.create_emoji_alias(
                alias_name=serializer.validated_data['alias_name'],
                original_emoji_id=serializer.validated_data['original_emoji_id'],
                workspace_id=int(workspace_id),
                created_by_id=request.user.id
            )
            return Response({
                'message': 'Emoji alias created',
                'emoji': CustomEmojiSerializer(alias).data
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CustomEmojiSearchView(APIView):
    """
    API view for searching custom emojis.
    """
    permission_classes = [IsAuthenticated]

    def __init__(self):
        super().__init__()
        self.emoji_service = EmojiService()

    @extend_schema(
        summary="Search custom emojis",
        parameters=[
            OpenApiParameter(name='workspace_id', description='Workspace ID', required=True, type=int),
            OpenApiParameter(name='q', description='Search query', required=True, type=str),
        ],
        responses={200: CustomEmojiSerializer(many=True)}
    )
    def get(self, request):
        """Search custom emojis by name."""
        workspace_id = request.query_params.get('workspace_id')
        query = request.query_params.get('q', '')

        if not workspace_id:
            return Response(
                {'error': 'workspace_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        emojis = self.emoji_service.search_emojis(int(workspace_id), query)
        serializer = CustomEmojiSerializer(emojis, many=True)
        return Response(serializer.data)


# ============================================
# Notification Views
# ============================================

class NotificationListView(APIView):
    """
    API view for listing and managing notifications.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def __init__(self):
        super().__init__()
        self.notification_service = NotificationService()

    @extend_schema(
        summary="List notifications",
        parameters=[
            OpenApiParameter(name='unread_only', description='Show only unread', required=False, type=bool),
            OpenApiParameter(name='limit', description='Max notifications to return', required=False, type=int),
        ],
        responses={200: NotificationListSerializer}
    )
    def get(self, request):
        """Get user's notifications."""
        unread_only = request.query_params.get('unread_only', 'false').lower() == 'true'
        limit = int(request.query_params.get('limit', 50))

        notifications = self.notification_service.notification_repo.get_user_notifications(
            request.user.id, unread_only=unread_only, limit=limit
        )
        unread_count = self.notification_service.notification_repo.get_unread_count(request.user.id)
        total_count = len(notifications)

        return Response({
            'notifications': NotificationSerializer(notifications, many=True).data,
            'unread_count': unread_count,
            'total_count': total_count
        })

    @extend_schema(
        summary="Mark notifications as read",
        request=MarkNotificationReadSerializer
    )
    def post(self, request):
        """Mark notifications as read."""
        serializer = MarkNotificationReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        notification_ids = serializer.validated_data.get('notification_ids', [])
        if notification_ids:
            count = 0
            for nid in notification_ids:
                if self.notification_service.notification_repo.mark_as_read(nid, request.user.id):
                    count += 1
            return Response({'message': f'{count} notifications marked as read'})
        else:
            # Mark all as read
            count = self.notification_service.notification_repo.mark_all_as_read(request.user.id)
            return Response({'message': f'{count} notifications marked as read'})


class NotificationDetailView(APIView):
    """
    API view for individual notification operations.
    """
    permission_classes = [IsAuthenticated]

    def __init__(self):
        super().__init__()
        self.notification_service = NotificationService()

    @extend_schema(
        summary="Mark notification as read",
        responses={200: NotificationSerializer}
    )
    def post(self, request, notification_id):
        """Mark a notification as read."""
        if self.notification_service.notification_repo.mark_as_read(notification_id, request.user.id):
            notification = self.notification_service.notification_repo.get_by_id(notification_id)
            return Response(NotificationSerializer(notification).data)
        return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(summary="Delete notification")
    def delete(self, request, notification_id):
        """Delete a notification."""
        if self.notification_service.notification_repo.delete_notification(notification_id, request.user.id):
            return Response({'message': 'Notification deleted'})
        return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)


class NotificationSettingsView(APIView):
    """
    API view for notification settings.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSettingsSerializer

    def __init__(self):
        super().__init__()
        self.notification_service = NotificationService()

    @extend_schema(
        summary="Get notification settings",
        responses={200: NotificationSettingsSerializer}
    )
    def get(self, request):
        """Get current user's notification settings."""
        settings = self.notification_service.get_user_settings(request.user.id)
        return Response(NotificationSettingsSerializer(settings).data)

    @extend_schema(
        summary="Update notification settings",
        request=NotificationSettingsUpdateSerializer,
        responses={200: NotificationSettingsSerializer}
    )
    def patch(self, request):
        """Update notification settings."""
        serializer = NotificationSettingsUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        settings = self.notification_service.update_user_settings(
            request.user.id, **serializer.validated_data
        )
        return Response(NotificationSettingsSerializer(settings).data)


class UnreadCountView(APIView):
    """
    API view for unread counts.
    """
    permission_classes = [IsAuthenticated]

    def __init__(self):
        super().__init__()
        self.notification_service = NotificationService()

    @extend_schema(
        summary="Get unread counts",
        responses={200: UnreadSummarySerializer}
    )
    def get(self, request):
        """Get unread message counts for all channels."""
        summary = self.notification_service.get_unread_counts(request.user.id)
        return Response(summary)

    @extend_schema(summary="Mark all channels as read")
    def post(self, request):
        """Mark all channels as read for the user."""
        count = self.notification_service.unread_repo.reset_all_unreads(request.user.id)
        return Response({'message': f'{count} channels marked as read'})


class ChannelUnreadView(APIView):
    """
    API view for per-channel unread count.
    """
    permission_classes = [IsAuthenticated]

    def __init__(self):
        super().__init__()
        self.notification_service = NotificationService()

    @extend_schema(summary="Mark channel as read")
    def post(self, request, channel_id):
        """Mark a channel as read."""
        if self.notification_service.mark_channel_read(request.user.id, channel_id):
            return Response({'message': 'Channel marked as read'})
        return Response({'error': 'Channel not found'}, status=status.HTTP_404_NOT_FOUND)


class KeywordAlertListView(APIView):
    """
    API view for keyword alerts.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = KeywordAlertSerializer

    def __init__(self):
        super().__init__()
        self.notification_service = NotificationService()

    @extend_schema(
        summary="List keyword alerts",
        responses={200: KeywordAlertSerializer(many=True)}
    )
    def get(self, request):
        """Get user's keyword alerts."""
        keywords = self.notification_service.get_user_keywords(request.user.id)
        return Response(KeywordAlertSerializer(keywords, many=True).data)

    @extend_schema(
        summary="Add keyword alert",
        request=KeywordAlertCreateSerializer,
        responses={201: KeywordAlertSerializer}
    )
    def post(self, request):
        """Add a keyword alert."""
        serializer = KeywordAlertCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        keyword = self.notification_service.add_keyword_alert(
            request.user.id,
            serializer.validated_data['keyword'],
            serializer.validated_data.get('workspace_id')
        )
        return Response(KeywordAlertSerializer(keyword).data, status=status.HTTP_201_CREATED)


class KeywordAlertDetailView(APIView):
    """
    API view for individual keyword alert operations.
    """
    permission_classes = [IsAuthenticated]

    def __init__(self):
        super().__init__()
        self.notification_service = NotificationService()

    @extend_schema(summary="Delete keyword alert")
    def delete(self, request, keyword_id):
        """Delete a keyword alert."""
        from core.models import KeywordAlert
        try:
            keyword = KeywordAlert.objects.get(id=keyword_id, user=request.user)
            keyword.delete()
            return Response({'message': 'Keyword alert deleted'})
        except KeywordAlert.DoesNotExist:
            return Response({'error': 'Keyword alert not found'}, status=status.HTTP_404_NOT_FOUND)


class MuteChannelView(APIView):
    """
    API view for muting/unmuting channels.
    """
    permission_classes = [IsAuthenticated]

    def __init__(self):
        super().__init__()
        self.notification_service = NotificationService()

    @extend_schema(summary="Mute channel")
    def post(self, request, channel_id):
        """Mute notifications for a channel."""
        if self.notification_service.mute_channel(request.user.id, channel_id):
            return Response({'message': 'Channel muted'})
        return Response({'error': 'Failed to mute channel'}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(summary="Unmute channel")
    def delete(self, request, channel_id):
        """Unmute notifications for a channel."""
        if self.notification_service.unmute_channel(request.user.id, channel_id):
            return Response({'message': 'Channel unmuted'})
        return Response({'error': 'Failed to unmute channel'}, status=status.HTTP_400_BAD_REQUEST)


class DoNotDisturbView(APIView):
    """
    API view for Do Not Disturb settings.
    """
    permission_classes = [IsAuthenticated]

    def __init__(self):
        super().__init__()
        self.notification_service = NotificationService()

    @extend_schema(summary="Get DND status")
    def get(self, request):
        """Get DND status."""
        settings = self.notification_service.get_user_settings(request.user.id)
        return Response({
            'dnd_enabled': settings.dnd_enabled,
            'dnd_start_time': settings.dnd_start_time,
            'dnd_end_time': settings.dnd_end_time,
            'is_currently_active': settings.is_dnd_active()
        })

    @extend_schema(summary="Set DND status")
    def post(self, request):
        """Set DND status."""
        enabled = request.data.get('enabled', False)
        start = request.data.get('start_time')
        end = request.data.get('end_time')

        settings = self.notification_service.set_dnd(request.user.id, enabled, start, end)
        return Response({
            'dnd_enabled': settings.dnd_enabled,
            'dnd_start_time': settings.dnd_start_time,
            'dnd_end_time': settings.dnd_end_time
        })
