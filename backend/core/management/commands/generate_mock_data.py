"""
Management command to generate mock data for testing.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker
import random
from datetime import timedelta

from core.models import (
    User, UserType,
    Workspace, WorkspaceMembership, WorkspaceRole,
    Channel, ChannelMembership, ChannelRole, ChannelType,
    ChannelSection, ChannelSectionItem,
    Message, MessageEditHistory,
    MessageReaction, CustomEmoji,
    Notification, NotificationSettings, UnreadCount, KeywordAlert
)


class Command(BaseCommand):
    help = 'Generate mock data for users, workspaces, and channels'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=20,
            help='Number of regular users to create (default: 20)'
        )
        parser.add_argument(
            '--workspaces',
            type=int,
            default=5,
            help='Number of workspaces to create (default: 5)'
        )
        parser.add_argument(
            '--channels-per-workspace',
            type=int,
            default=3,
            help='Number of channels per workspace (default: 3)'
        )
        parser.add_argument(
            '--messages-per-channel',
            type=int,
            default=10,
            help='Number of messages per channel (default: 10)'
        )
        parser.add_argument(
            '--replies-per-thread',
            type=int,
            default=5,
            help='Max replies per thread (default: 5)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='Test@123456',
            help='Password for all users (default: Test@123456)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before generating new data'
        )

    def handle(self, *args, **options):
        fake = Faker()
        password = options['password']
        num_users = options['users']
        num_workspaces = options['workspaces']
        channels_per_workspace = options['channels_per_workspace']
        messages_per_channel = options['messages_per_channel']
        replies_per_thread = options['replies_per_thread']
        clear = options['clear']

        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('Mock Data Generator'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'Users to create: {num_users}')
        self.stdout.write(f'Workspaces to create: {num_workspaces}')
        self.stdout.write(f'Channels per workspace: {channels_per_workspace}')
        self.stdout.write(f'Messages per channel: {messages_per_channel}')
        self.stdout.write(f'Max replies per thread: {replies_per_thread}')
        self.stdout.write(f'Password for all users: {password}')
        self.stdout.write('=' * 60)

        with transaction.atomic():
            # Clear existing data if requested
            if clear:
                self.stdout.write('Clearing existing data...')
                ChannelMembership.objects.all().delete()
                Channel.objects.all().delete()
                WorkspaceMembership.objects.all().delete()
                Workspace.objects.all().delete()
                User.objects.exclude(user_type=UserType.ADMIN.value).delete()
                self.stdout.write(self.style.WARNING('Existing data cleared.'))

            # Create dummy users for each type (if not exists)
            self._create_dummy_users(password)

            # Get admin user for creating workspaces
            admin_user = User.objects.filter(user_type=UserType.ADMIN.value).first()
            super_user = User.objects.filter(user_type=UserType.SUPER_USER.value).first()

            # Create regular users
            self.stdout.write(f'\nCreating {num_users} regular users...')
            regular_users = []
            for i in range(num_users):
                user = User.objects.create_user(
                    email=fake.email(),
                    username=fake.user_name() + str(i),
                    password=password,
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    user_type=UserType.USER.value,
                    job_title=fake.job(),
                    department=random.choice(['Engineering', 'Marketing', 'Sales', 'HR', 'Finance', 'Operations']),
                    phone=fake.phone_number()[:20],
                )
                regular_users.append(user)
                if (i + 1) % 5 == 0:
                    self.stdout.write(f'  Created {i + 1}/{num_users} users...')

            self.stdout.write(self.style.SUCCESS(f'Created {len(regular_users)} regular users'))

            # Create workspaces
            self.stdout.write(f'\nCreating {num_workspaces} workspaces...')
            workspaces = []
            workspace_creators = [admin_user, super_user] + random.sample(regular_users, min(3, len(regular_users)))

            for i in range(num_workspaces):
                workspace_name = fake.company() + f' {i+1}'
                creator = random.choice(workspace_creators)
                
                # Ensure creator can create workspaces
                if not (creator.is_admin() or creator.is_super_user_type()):
                    creator = admin_user

                workspace = Workspace.objects.create(
                    name=workspace_name,
                    description=fake.catch_phrase(),
                    owner=creator,
                    is_private=random.choice([True, False, False]),  # 33% private
                )
                
                # Add owner as member
                WorkspaceMembership.objects.create(
                    user=creator,
                    workspace=workspace,
                    role=WorkspaceRole.OWNER.value
                )
                
                workspaces.append(workspace)
                self.stdout.write(f'  Created workspace: {workspace_name}')

            self.stdout.write(self.style.SUCCESS(f'Created {len(workspaces)} workspaces'))

            # Add members to workspaces
            self.stdout.write(f'\nAdding members to workspaces...')
            all_users = list(User.objects.filter(is_active=True))

            for workspace in workspaces:
                # Add random members to each workspace
                num_members = random.randint(5, min(15, len(all_users)))
                members_to_add = random.sample(all_users, num_members)
                
                for user in members_to_add:
                    if not WorkspaceMembership.objects.filter(workspace=workspace, user=user).exists():
                        role = random.choices(
                            [WorkspaceRole.ADMIN.value, WorkspaceRole.MEMBER.value, WorkspaceRole.GUEST.value],
                            weights=[15, 70, 15]
                        )[0]
                        WorkspaceMembership.objects.create(
                            user=user,
                            workspace=workspace,
                            role=role
                        )

            self.stdout.write(self.style.SUCCESS('Added members to all workspaces'))

            # Create channels for each workspace
            self.stdout.write(f'\nCreating channels for each workspace...')
            total_channels = 0

            for workspace in workspaces:
                workspace_members = list(WorkspaceMembership.objects.filter(workspace=workspace))
                
                for j in range(channels_per_workspace):
                    channel_name = fake.word() + '-' + fake.word()
                    channel_type = random.choices(
                        [ChannelType.PUBLIC.value, ChannelType.PRIVATE.value],
                        weights=[70, 30]
                    )[0]
                    
                    creator = random.choice(workspace_members).user
                    
                    channel = Channel.objects.create(
                        name=channel_name,
                        description=fake.sentence(),
                        topic=fake.sentence(nb_words=6),
                        workspace=workspace,
                        created_by=creator,
                        channel_type=channel_type,
                    )
                    
                    # Add creator as owner
                    ChannelMembership.objects.create(
                        user=creator,
                        channel=channel,
                        role=ChannelRole.OWNER.value
                    )
                    
                    # Add some members to the channel
                    num_channel_members = random.randint(3, min(10, len(workspace_members)))
                    channel_members = random.sample(workspace_members, num_channel_members)
                    
                    for membership in channel_members:
                        if membership.user != creator:
                            ChannelMembership.objects.create(
                                user=membership.user,
                                channel=channel,
                                role=ChannelRole.MEMBER.value
                            )
                    
                    total_channels += 1

            self.stdout.write(self.style.SUCCESS(f'Created {total_channels} channels'))

            # Create some direct message channels
            self.stdout.write(f'\nCreating direct message channels...')
            dm_count = 0
            for workspace in workspaces[:3]:  # Only for first 3 workspaces
                workspace_member_ids = list(WorkspaceMembership.objects.filter(
                    workspace=workspace
                ).values_list('user_id', flat=True))
                
                # Create a few DM channels
                for _ in range(min(3, len(workspace_member_ids) // 2)):
                    if len(workspace_member_ids) >= 2:
                        user1_id, user2_id = random.sample(workspace_member_ids, 2)
                        user1 = User.objects.get(id=user1_id)
                        user2 = User.objects.get(id=user2_id)
                        
                        channel_name = f"dm-{min(user1_id, user2_id)}-{max(user1_id, user2_id)}"
                        
                        # Check if DM already exists
                        if not Channel.objects.filter(
                            name=channel_name,
                            workspace=workspace,
                            channel_type=ChannelType.DIRECT.value
                        ).exists():
                            dm_channel = Channel.objects.create(
                                name=channel_name,
                                workspace=workspace,
                                created_by=user1,
                                channel_type=ChannelType.DIRECT.value,
                                dm_with=user2
                            )
                            
                            ChannelMembership.objects.create(
                                user=user1,
                                channel=dm_channel,
                                role=ChannelRole.OWNER.value
                            )
                            ChannelMembership.objects.create(
                                user=user2,
                                channel=dm_channel,
                                role=ChannelRole.MEMBER.value
                            )
                            dm_count += 1

            self.stdout.write(self.style.SUCCESS(f'Created {dm_count} direct message channels'))

            # Create messages for channels
            self.stdout.write(f'\nCreating messages for channels...')
            total_messages = 0
            total_threads = 0
            
            channels = Channel.objects.filter(channel_type__in=[ChannelType.PUBLIC.value, ChannelType.PRIVATE.value])
            
            for channel in channels:
                channel_members = list(ChannelMembership.objects.filter(channel=channel))
                if not channel_members:
                    continue
                
                # Create top-level messages
                for _ in range(messages_per_channel):
                    sender = random.choice(channel_members).user
                    message = Message.objects.create(
                        content=fake.paragraph(nb_sentences=random.randint(1, 5)),
                        sender=sender,
                        channel=channel,
                    )
                    total_messages += 1
                    
                    # Randomly create thread replies (50% chance)
                    if random.random() < 0.5:
                        num_replies = random.randint(1, replies_per_thread)
                        for _ in range(num_replies):
                            reply_sender = random.choice(channel_members).user
                            Message.objects.create(
                                content=fake.sentence(),
                                sender=reply_sender,
                                channel=channel,
                                parent_message=message
                            )
                            total_threads += 1
                
                # Create some DM messages
                dm_channels = Channel.objects.filter(channel_type=ChannelType.DIRECT.value)
                for dm_channel in dm_channels:
                    dm_members = list(ChannelMembership.objects.filter(channel=dm_channel))
                    if len(dm_members) >= 2:
                        for _ in range(random.randint(3, 8)):
                            sender = random.choice(dm_members).user
                            Message.objects.create(
                                content=fake.sentence(),
                                sender=sender,
                                channel=dm_channel,
                                dm_recipient=dm_members[0].user if sender == dm_members[1].user else dm_members[1].user
                            )
                            total_messages += 1

            self.stdout.write(self.style.SUCCESS(f'Created {total_messages} messages'))
            self.stdout.write(self.style.SUCCESS(f'Created {total_threads} thread replies'))

            # Create some edited messages with history
            self.stdout.write(f'\nCreating edited messages with history...')
            edited_count = 0
            for _ in range(min(20, total_messages // 2)):
                message = Message.objects.filter(
                    is_edited=False,
                    parent_message__isnull=True,
                    channel__isnull=False
                ).order_by('?').first()
                
                if message:
                    # Save old content
                    MessageEditHistory.objects.create(
                        message=message,
                        old_content=message.content,
                        edited_by=message.sender
                    )
                    # Update message
                    message.content = fake.paragraph(nb_sentences=2) + " [EDITED]"
                    message.is_edited = True
                    message.edited_at = timezone.now()
                    message.save()
                    edited_count += 1

            self.stdout.write(self.style.SUCCESS(f'Created {edited_count} edited messages with history'))

            # Create channel sections for users
            self.stdout.write(f'\nCreating channel sections for users...')
            section_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F']

            for user in all_users:
                # Create default sections for each user in each workspace
                for workspace in workspaces:
                    # Check if user is member of workspace
                    if not WorkspaceMembership.objects.filter(user=user, workspace=workspace).exists():
                        continue

                    # Create default sections
                    starred_section = ChannelSection.objects.create(
                        user=user,
                        workspace=workspace,
                        name='Starred',
                        section_type='starred',
                        order=0
                    )

                    channels_section = ChannelSection.objects.create(
                        user=user,
                        workspace=workspace,
                        name='Channels',
                        section_type='channels',
                        order=1
                    )

                    dm_section = ChannelSection.objects.create(
                        user=user,
                        workspace=workspace,
                        name='Direct Messages',
                        section_type='direct_messages',
                        order=2
                    )

                    # Create 1-2 custom sections for some users
                    if random.random() < 0.7:  # 70% chance
                        custom_section = ChannelSection.objects.create(
                            user=user,
                            workspace=workspace,
                            name=random.choice(['Projects', 'Team', 'Important', 'Archive']),
                            section_type='custom',
                            color=random.choice(section_colors),
                            order=3
                        )

                        # Add some channels to custom section
                        workspace_channels = list(Channel.objects.filter(workspace=workspace, is_active=True))
                        if workspace_channels:
                            num_in_custom = random.randint(1, min(3, len(workspace_channels)))
                            for idx, ch in enumerate(random.sample(workspace_channels, num_in_custom)):
                                ChannelSectionItem.objects.create(
                                    section=custom_section,
                                    channel=ch,
                                    order=idx
                                )

                    # Add remaining channels to 'Channels' section
                    all_workspace_channels = set(Channel.objects.filter(workspace=workspace, is_active=True).values_list('id', flat=True))
                    custom_section_channels = set(ChannelSectionItem.objects.filter(
                        section__user=user,
                        section__workspace=workspace
                    ).values_list('channel_id', flat=True))

                    remaining_channels = list(all_workspace_channels - custom_section_channels)
                    for idx, channel_id in enumerate(remaining_channels):
                        channel = Channel.objects.get(id=channel_id)
                        ChannelSectionItem.objects.create(
                            section=channels_section,
                            channel=channel,
                            order=idx
                        )

            self.stdout.write(self.style.SUCCESS('Created channel sections for all users'))

            # Create emoji reactions on messages
            self.stdout.write(f'\nCreating emoji reactions on messages...')
            common_emojis = ['👍', '❤️', '😂', '🎉', '🚀', '👀', '✅', '🔥']

            all_messages = list(Message.objects.filter(is_deleted=False))
            for message in all_messages:
                # Add 0-5 random reactions per message
                num_reactions = random.randint(0, 5)
                if num_reactions > 0:
                    selected_emojis = random.sample(common_emojis, num_reactions)
                    for emoji in selected_emojis:
                        # 1-3 users react with each emoji
                        num_users = random.randint(1, 3)
                        potential_users = list(User.objects.filter(is_active=True))
                        reacting_users = random.sample(potential_users, min(num_users, len(potential_users)))

                        for user in reacting_users:
                            # Skip if already reacted
                            if not MessageReaction.objects.filter(
                                message=message,
                                user=user,
                                emoji=emoji
                            ).exists():
                                MessageReaction.objects.create(
                                    message=message,
                                    user=user,
                                    emoji=emoji
                                )

            self.stdout.write(self.style.SUCCESS(f'Created {MessageReaction.objects.count()} emoji reactions'))

            # Create notification settings and unread counts for users
            self.stdout.write(f'\nCreating notification settings and unread counts...')
            all_channels = list(Channel.objects.filter(is_active=True))

            for user in all_users:
                # Create notification settings
                settings, created = NotificationSettings.objects.get_or_create(
                    user=user,
                    defaults={
                        'all_notifications_enabled': True,
                        'desktop_notifications': True,
                        'mobile_notifications': True,
                        'email_notifications': random.choice([True, False]),
                        'sound_enabled': True,
                        'mention_notifications': True,
                        'dm_notifications': True,
                        'thread_notifications': random.choice(['all', 'mentions', 'none']),
                        'reaction_notifications': True,
                        'keyword_notifications': True,
                        'dnd_enabled': False,
                    }
                )

                # Create unread counts for some channels
                user_channels = list(ChannelMembership.objects.filter(
                    user=user
                ).values_list('channel_id', flat=True))

                for channel_id in random.sample(user_channels, min(3, len(user_channels))):
                    UnreadCount.objects.get_or_create(
                        user=user,
                        channel_id=channel_id,
                        defaults={'count': random.randint(1, 10)}
                    )

                # Add some keyword alerts
                keywords = ['alert', 'urgent', 'deadline', 'meeting', 'important']
                for keyword in random.sample(keywords, 2):
                    KeywordAlert.objects.get_or_create(
                        user=user,
                        keyword=keyword,
                        defaults={'notify_on_match': True}
                    )

            # Create some sample notifications
            self.stdout.write(f'Creating sample notifications...')
            notification_types = ['mention', 'dm', 'thread_reply', 'keyword_alert']
            all_messages = list(Message.objects.filter(is_deleted=False)[:20])

            for user in all_users[:3]:
                # Create 2-5 notifications per user
                num_notifications = random.randint(2, 5)
                for _ in range(num_notifications):
                    message = random.choice(all_messages) if all_messages else None
                    notif_type = random.choice(notification_types)

                    Notification.objects.create(
                        user=user,
                        notification_type=notif_type,
                        title=f"Sample {notif_type.replace('_', ' ')} notification",
                        body=f"This is a test notification for {notif_type}",
                        link=f"/messages/{message.id}" if message else "",
                        message=message,
                        channel=message.channel if message else None,
                        workspace=message.channel.workspace if message and message.channel else None,
                        triggered_by=random.choice(all_users) if all_users else None,
                        is_read=random.choice([True, False])
                    )

            self.stdout.write(self.style.SUCCESS(f'Created notification settings and sample data'))

        # Print summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('Summary:'))
        self.stdout.write(f'  Total Users: {User.objects.count()}')
        self.stdout.write(f'  Total Workspaces: {Workspace.objects.count()}')
        self.stdout.write(f'  Total Channels: {Channel.objects.count()}')
        self.stdout.write(f'  Total Workspace Memberships: {WorkspaceMembership.objects.count()}')
        self.stdout.write(f'  Total Channel Memberships: {ChannelMembership.objects.count()}')
        self.stdout.write(f'  Total Messages: {Message.objects.count()}')
        self.stdout.write(f'  Total Thread Replies: {Message.objects.filter(parent_message__isnull=False).count()}')
        self.stdout.write(f'  Total Edit History: {MessageEditHistory.objects.count()}')
        self.stdout.write(f'  Total Channel Sections: {ChannelSection.objects.count()}')
        self.stdout.write(f'  Total Channel Section Items: {ChannelSectionItem.objects.count()}')
        self.stdout.write(f'  Total Emoji Reactions: {MessageReaction.objects.count()}')
        self.stdout.write(f'  Total Notifications: {Notification.objects.count()}')
        self.stdout.write(f'  Total Unread Counts: {UnreadCount.objects.count()}')
        self.stdout.write(f'  Total Keyword Alerts: {KeywordAlert.objects.count()}')
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('\nMock data generated successfully!'))

    def _create_dummy_users(self, password):
        """Create dummy users for each user type."""
        self.stdout.write('\nEnsuring dummy users exist...')
        
        dummy_users = [
            {
                'email': 'admin@slackclone.com',
                'username': 'admin',
                'first_name': 'System',
                'last_name': 'Admin',
                'user_type': UserType.ADMIN.value,
                'is_staff': True,
                'is_superuser': True,
                'job_title': 'System Administrator',
                'department': 'IT Department',
            },
            {
                'email': 'superuser@slackclone.com',
                'username': 'superuser',
                'first_name': 'Super',
                'last_name': 'User',
                'user_type': UserType.SUPER_USER.value,
                'is_staff': True,
                'job_title': 'Platform Manager',
                'department': 'Management',
            },
            {
                'email': 'superworkspaceuser@slackclone.com',
                'username': 'superworkspaceuser',
                'first_name': 'Super Workspace',
                'last_name': 'User',
                'user_type': UserType.SUPER_WORKSPACE_USER.value,
                'job_title': 'Workspace Manager',
                'department': 'Operations',
            },
            {
                'email': 'user@slackclone.com',
                'username': 'regularuser',
                'first_name': 'Regular',
                'last_name': 'User',
                'user_type': UserType.USER.value,
                'job_title': 'Team Member',
                'department': 'Engineering',
            },
        ]
        
        for user_data in dummy_users:
            email = user_data['email']
            if not User.objects.filter(email=email).exists():
                User.objects.create_user(
                    email=email,
                    username=user_data['username'],
                    password=password,
                    **{k: v for k, v in user_data.items() if k not in ['email', 'username']}
                )
                self.stdout.write(f'  Created: {email}')
            else:
                self.stdout.write(f'  Exists: {email}')
