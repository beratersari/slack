"""
Management command to create dummy users for each user type.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import User, UserType


class Command(BaseCommand):
    help = 'Create dummy users for each user type (Admin, Super User, Super Group User, User)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            type=str,
            default='Test@123456',
            help='Password for all dummy users (default: Test@123456)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if users already exist'
        )

    def handle(self, *args, **options):
        password = options['password']
        force = options['force']
        
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
        
        created_count = 0
        skipped_count = 0
        
        with transaction.atomic():
            for user_data in dummy_users:
                email = user_data['email']
                username = user_data['username']
                
                # Check if user already exists
                existing_user = User.objects.filter(email=email).first()
                
                if existing_user:
                    if force:
                        # Update existing user
                        for key, value in user_data.items():
                            if key not in ['email', 'username']:
                                setattr(existing_user, key, value)
                        existing_user.set_password(password)
                        existing_user.save()
                        self.stdout.write(
                            self.style.WARNING(f'Updated user: {email} ({user_data["user_type"]})')
                        )
                        created_count += 1
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'User already exists: {email} - skipping')
                        )
                        skipped_count += 1
                    continue
                
                # Create new user
                user = User.objects.create_user(
                    email=email,
                    username=username,
                    password=password,
                    **{k: v for k, v in user_data.items() if k not in ['email', 'username']}
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Created user: {email} ({user_data["user_type"]})')
                )
                created_count += 1
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS(f'Summary:'))
        self.stdout.write(self.style.SUCCESS(f'  Created/Updated: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'  Skipped: {skipped_count}'))
        self.stdout.write(self.style.SUCCESS(f'  Password: {password}'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write('')
        self.stdout.write('Dummy users created successfully!')
        self.stdout.write('')
        self.stdout.write('User credentials:')
        for user_data in dummy_users:
            self.stdout.write(f'  - {user_data["email"]} ({user_data["user_type"]})')
