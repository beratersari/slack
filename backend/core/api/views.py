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

from core.models import User, UserType, Group, GroupRole, Channel, ChannelType, ChannelRole
from core.services import AuthService, UserService, GroupService, ChannelService, MessageService
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    LoginSerializer, LoginResponseSerializer, RegisterSerializer,
    ChangePasswordSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, TokenRefreshSerializer,
    UserTypeSerializer,
    # Group serializers
    GroupSerializer, GroupCreateSerializer, GroupUpdateSerializer,
    GroupMembershipSerializer, GroupAddMemberSerializer, GroupMembershipUpdateSerializer,
    # Channel serializers
    ChannelSerializer, ChannelCreateSerializer, ChannelUpdateSerializer,
    ChannelMembershipSerializer, ChannelAddMemberSerializer, DirectMessageSerializer,
    # Message serializers
    MessageSerializer, MessageDetailSerializer, MessageEditHistorySerializer,
    MessageCreateSerializer, MessageReplySerializer, MessageEditSerializer,
    DirectMessageCreateSerializer, DMConversationSerializer
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
# Group Views
# ============================================

class GroupListView(APIView):
    """
    API view for listing and creating groups.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.group_service = GroupService()
    
    @extend_schema(
        summary="List groups",
        description="Returns groups the user is a member of (or all groups for admins)",
        responses={200: GroupSerializer(many=True)}
    )
    def get(self, request):
        """Get list of groups."""
        if request.user.is_admin() or request.user.is_super_user_type():
            groups = self.group_service.get_active_groups()
        else:
            groups = self.group_service.get_groups_by_member(request.user.id)
        
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Create group",
        description="Create a new group (admin/super user only)",
        request=GroupCreateSerializer,
        responses={201: GroupSerializer}
    )
    def post(self, request):
        """Create a new group."""
        serializer = GroupCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            group = self.group_service.create_group(
                name=serializer.validated_data['name'],
                owner_id=request.user.id,
                description=serializer.validated_data.get('description', ''),
                is_private=serializer.validated_data.get('is_private', False),
                icon=serializer.validated_data.get('icon'),
                workspace_url=serializer.validated_data.get('workspace_url'),
            )
            
            return Response({
                'message': 'Group created successfully',
                'group': GroupSerializer(group).data
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GroupDetailView(APIView):
    """
    API view for individual group operations.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.group_service = GroupService()
    
    @extend_schema(summary="Get group by ID", responses={200: GroupSerializer})
    def get(self, request, group_id):
        """Get group by ID."""
        group = self.group_service.get_group_by_id(group_id)
        if not group:
            return Response({'error': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check access
        if group.is_private and not self.group_service.is_member(group_id, request.user.id):
            if not (request.user.is_admin() or request.user.is_super_user_type()):
                return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = GroupSerializer(group)
        return Response(serializer.data)
    
    @extend_schema(summary="Update group", request=GroupUpdateSerializer)
    def patch(self, request, group_id):
        """Update group."""
        serializer = GroupUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            group = self.group_service.update_group(
                group_id=group_id,
                user_id=request.user.id,
                **serializer.validated_data
            )
            return Response({
                'message': 'Group updated successfully',
                'group': GroupSerializer(group).data
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(summary="Delete group")
    def delete(self, request, group_id):
        """Delete group."""
        try:
            self.group_service.delete_group(group_id, request.user.id)
            return Response({'message': 'Group deleted successfully'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GroupMembersView(APIView):
    """
    API view for group membership operations.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.group_service = GroupService()
    
    @extend_schema(summary="Get group members", responses={200: GroupMembershipSerializer(many=True)})
    def get(self, request, group_id):
        """Get all members of a group."""
        members = self.group_service.get_group_members(group_id)
        serializer = GroupMembershipSerializer(members, many=True)
        return Response(serializer.data)
    
    @extend_schema(summary="Add member to group", request=GroupAddMemberSerializer)
    def post(self, request, group_id):
        """Add a member to a group."""
        serializer = GroupAddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            membership = self.group_service.add_member(
                group_id=group_id,
                user_id=serializer.validated_data['user_id'],
                added_by_id=request.user.id,
                role=serializer.validated_data.get('role', GroupRole.MEMBER.value)
            )
            return Response({
                'message': 'Member added successfully',
                'membership': GroupMembershipSerializer(membership).data
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GroupMemberDetailView(APIView):
    """
    API view for individual group member operations.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.group_service = GroupService()
    
    @extend_schema(summary="Update member role", request=GroupMembershipUpdateSerializer)
    def patch(self, request, group_id, user_id):
        """Update a member's role."""
        serializer = GroupMembershipUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            membership = self.group_service.update_member_role(
                group_id=group_id,
                user_id=user_id,
                new_role=serializer.validated_data['role'],
                updated_by_id=request.user.id
            )
            return Response({
                'message': 'Member role updated',
                'membership': GroupMembershipSerializer(membership).data
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(summary="Remove member from group")
    def delete(self, request, group_id, user_id):
        """Remove a member from a group."""
        try:
            self.group_service.remove_member(
                group_id=group_id,
                user_id=user_id,
                removed_by_id=request.user.id
            )
            return Response({'message': 'Member removed successfully'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GroupSearchView(APIView):
    """
    API view for searching groups.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.group_service = GroupService()
    
    @extend_schema(
        summary="Search groups",
        parameters=[OpenApiParameter(name='q', description='Search query', required=True, type=str)],
        responses={200: GroupSerializer(many=True)}
    )
    def get(self, request):
        """Search groups by query."""
        query = request.query_params.get('q', '')
        groups = self.group_service.search_groups(query, request.user.id)
        serializer = GroupSerializer(groups, many=True)
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
        parameters=[OpenApiParameter(name='group_id', description='Filter by group ID', required=False, type=int)],
        responses={200: ChannelSerializer(many=True)}
    )
    def get(self, request):
        """Get list of channels."""
        group_id = request.query_params.get('group_id')
        
        if request.user.is_admin() or request.user.is_super_user_type():
            if group_id:
                channels = self.channel_service.get_channels_by_group(int(group_id))
            else:
                channels = self.channel_service.get_active_channels()
        else:
            channels = self.channel_service.get_channels_by_member(request.user.id)
            if group_id:
                channels = [c for c in channels if c.group_id == int(group_id)]
        
        serializer = ChannelSerializer(channels, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Create channel",
        description="Create a new channel (admin/super user/group admin only)",
        request=ChannelCreateSerializer,
        responses={201: ChannelSerializer}
    )
    def post(self, request):
        """Create a new channel."""
        serializer = ChannelCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            channel = self.channel_service.create_channel(
                name=serializer.validated_data['name'],
                group_id=serializer.validated_data['group_id'],
                created_by_id=request.user.id,
                channel_type=serializer.validated_data.get('channel_type', ChannelType.PUBLIC.value),
                description=serializer.validated_data.get('description', ''),
                topic=serializer.validated_data.get('topic', ''),
            )
            
            return Response({
                'message': 'Channel created successfully',
                'channel': ChannelSerializer(channel).data
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
    
    @extend_schema(summary="Get channel by ID", responses={200: ChannelSerializer})
    def get(self, request, channel_id):
        """Get channel by ID."""
        channel = self.channel_service.get_channel_by_id(channel_id)
        if not channel:
            return Response({'error': 'Channel not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check access for private channels
        if channel.is_private() and not self.channel_service.is_member(channel_id, request.user.id):
            if not (request.user.is_admin() or request.user.is_super_user_type()):
                return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ChannelSerializer(channel)
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
                'channel': ChannelSerializer(channel).data
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
    
    @extend_schema(summary="Get channel members", responses={200: ChannelMembershipSerializer(many=True)})
    def get(self, request, channel_id):
        """Get all members of a channel."""
        members = self.channel_service.get_channel_members(channel_id)
        serializer = ChannelMembershipSerializer(members, many=True)
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
    
    @extend_schema(summary="Join a public channel")
    def post(self, request, channel_id):
        """Join a public channel."""
        try:
            membership = self.channel_service.join_public_channel(channel_id, request.user.id)
            return Response({
                'message': 'Joined channel successfully',
                'membership': ChannelMembershipSerializer(membership).data
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
            OpenApiParameter(name='group_id', description='Filter by group ID', required=False, type=int)
        ],
        responses={200: ChannelSerializer(many=True)}
    )
    def get(self, request):
        """Search channels by query."""
        query = request.query_params.get('q', '')
        group_id = request.query_params.get('group_id')
        
        channels = self.channel_service.search_channels(
            query=query,
            group_id=int(group_id) if group_id else None,
            user_id=request.user.id
        )
        serializer = ChannelSerializer(channels, many=True)
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
        responses={200: ChannelSerializer}
    )
    def post(self, request):
        """Get or create a direct message channel."""
        serializer = DirectMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            channel = self.channel_service.get_or_create_dm_channel(
                user1_id=request.user.id,
                user2_id=serializer.validated_data['user_id'],
                group_id=serializer.validated_data['group_id']
            )
            return Response({
                'message': 'Direct message channel ready',
                'channel': ChannelSerializer(channel).data
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
        responses={200: MessageSerializer(many=True)}
    )
    def get(self, request, channel_id):
        """Get all messages in a channel (top-level, not replies)."""
        try:
            messages = self.message_service.get_channel_messages(channel_id, request.user)
            serializer = MessageSerializer(messages, many=True)
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
        responses={200: MessageSerializer(many=True)}
    )
    def get(self, request, message_id):
        """Get all replies in a thread."""
        try:
            replies = self.message_service.get_thread_replies(message_id, request.user)
            serializer = MessageSerializer(replies, many=True)
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
        responses={200: MessageSerializer(many=True)}
    )
    def get(self, request, user_id):
        """Get DM conversation with a specific user."""
        try:
            messages = self.message_service.get_dm_conversation(request.user, user_id)
            serializer = MessageSerializer(messages, many=True)
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
        responses={200: MessageSerializer(many=True)}
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
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
