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
    Group, GroupMembership, GroupRole,
    Channel, ChannelMembership, ChannelRole, ChannelType,
    Message, MessageEditHistory
)


class Command(BaseCommand):
    help = 'Generate mock data for users, groups, and channels'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=20,
            help='Number of regular users to create (default: 20)'
        )
        parser.add_argument(
            '--groups',
            type=int,
            default=5,
            help='Number of groups to create (default: 5)'
        )
        parser.add_argument(
            '--channels-per-group',
            type=int,
            default=3,
            help='Number of channels per group (default: 3)'
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
        num_groups = options['groups']
        channels_per_group = options['channels_per_group']
        messages_per_channel = options['messages_per_channel']
        replies_per_thread = options['replies_per_thread']
        clear = options['clear']

        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('Mock Data Generator'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'Users to create: {num_users}')
        self.stdout.write(f'Groups to create: {num_groups}')
        self.stdout.write(f'Channels per group: {channels_per_group}')
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
                GroupMembership.objects.all().delete()
                Group.objects.all().delete()
                User.objects.exclude(user_type=UserType.ADMIN.value).delete()
                self.stdout.write(self.style.WARNING('Existing data cleared.'))

            # Create dummy users for each type (if not exists)
            self._create_dummy_users(password)

            # Get admin user for creating groups
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

            # Create groups
            self.stdout.write(f'\nCreating {num_groups} groups...')
            groups = []
            group_creators = [admin_user, super_user] + random.sample(regular_users, min(3, len(regular_users)))

            for i in range(num_groups):
                group_name = fake.company() + f' {i+1}'
                creator = random.choice(group_creators)
                
                # Ensure creator can create groups
                if not (creator.is_admin() or creator.is_super_user_type()):
                    creator = admin_user

                group = Group.objects.create(
                    name=group_name,
                    description=fake.catch_phrase(),
                    owner=creator,
                    is_private=random.choice([True, False, False]),  # 33% private
                )
                
                # Add owner as member
                GroupMembership.objects.create(
                    user=creator,
                    group=group,
                    role=GroupRole.OWNER.value
                )
                
                groups.append(group)
                self.stdout.write(f'  Created group: {group_name}')

            self.stdout.write(self.style.SUCCESS(f'Created {len(groups)} groups'))

            # Add members to groups
            self.stdout.write(f'\nAdding members to groups...')
            all_users = list(User.objects.filter(is_active=True))

            for group in groups:
                # Add random members to each group
                num_members = random.randint(5, min(15, len(all_users)))
                members_to_add = random.sample(all_users, num_members)
                
                for user in members_to_add:
                    if not GroupMembership.objects.filter(group=group, user=user).exists():
                        role = random.choices(
                            [GroupRole.ADMIN.value, GroupRole.MEMBER.value, GroupRole.GUEST.value],
                            weights=[15, 70, 15]
                        )[0]
                        GroupMembership.objects.create(
                            user=user,
                            group=group,
                            role=role
                        )

            self.stdout.write(self.style.SUCCESS('Added members to all groups'))

            # Create channels for each group
            self.stdout.write(f'\nCreating channels for each group...')
            total_channels = 0

            for group in groups:
                group_members = list(GroupMembership.objects.filter(group=group))
                
                for j in range(channels_per_group):
                    channel_name = fake.word() + '-' + fake.word()
                    channel_type = random.choices(
                        [ChannelType.PUBLIC.value, ChannelType.PRIVATE.value],
                        weights=[70, 30]
                    )[0]
                    
                    creator = random.choice(group_members).user
                    
                    channel = Channel.objects.create(
                        name=channel_name,
                        description=fake.sentence(),
                        topic=fake.sentence(nb_words=6),
                        group=group,
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
                    num_channel_members = random.randint(3, min(10, len(group_members)))
                    channel_members = random.sample(group_members, num_channel_members)
                    
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
            for group in groups[:3]:  # Only for first 3 groups
                group_member_ids = list(GroupMembership.objects.filter(
                    group=group
                ).values_list('user_id', flat=True))
                
                # Create a few DM channels
                for _ in range(min(3, len(group_member_ids) // 2)):
                    if len(group_member_ids) >= 2:
                        user1_id, user2_id = random.sample(group_member_ids, 2)
                        user1 = User.objects.get(id=user1_id)
                        user2 = User.objects.get(id=user2_id)
                        
                        channel_name = f"dm-{min(user1_id, user2_id)}-{max(user1_id, user2_id)}"
                        
                        # Check if DM already exists
                        if not Channel.objects.filter(
                            name=channel_name,
                            group=group,
                            channel_type=ChannelType.DIRECT.value
                        ).exists():
                            dm_channel = Channel.objects.create(
                                name=channel_name,
                                group=group,
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

        # Print summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('Summary:'))
        self.stdout.write(f'  Total Users: {User.objects.count()}')
        self.stdout.write(f'  Total Groups: {Group.objects.count()}')
        self.stdout.write(f'  Total Channels: {Channel.objects.count()}')
        self.stdout.write(f'  Total Group Memberships: {GroupMembership.objects.count()}')
        self.stdout.write(f'  Total Channel Memberships: {ChannelMembership.objects.count()}')
        self.stdout.write(f'  Total Messages: {Message.objects.count()}')
        self.stdout.write(f'  Total Thread Replies: {Message.objects.filter(parent_message__isnull=False).count()}')
        self.stdout.write(f'  Total Edit History: {MessageEditHistory.objects.count()}')
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
                'email': 'supergroupuser@slackclone.com',
                'username': 'supergroupuser',
                'first_name': 'Super Group',
                'last_name': 'User',
                'user_type': UserType.SUPER_GROUP_USER.value,
                'job_title': 'Group Manager',
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
