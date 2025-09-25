from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from admin_panel.models import AdminProfile, SystemSettings
from django.db import transaction

class Command(BaseCommand):
    help = 'Setup initial admin configuration for AURA'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Admin username', default='admin')
        parser.add_argument('--email', type=str, help='Admin email', default='admin@aura.com')
        parser.add_argument('--password', type=str, help='Admin password', default='admin123')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        
        try:
            with transaction.atomic():
                # Create superuser if doesn't exist
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'is_staff': True,
                        'is_superuser': True,
                        'first_name': 'AURA',
                        'last_name': 'Administrator'
                    }
                )
                
                if created:
                    user.set_password(password)
                    user.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Created superuser: {username}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ Superuser {username} already exists')
                    )
                
                # Create admin profile
                admin_profile, created = AdminProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'role': 'super_admin',
                        'department': 'System Administration',
                        'phone_number': '+1-555-0123',
                        'is_active_admin': True,
                        'permissions': {
                            'can_manage_users': True,
                            'can_manage_events': True,
                            'can_view_analytics': True,
                            'can_manage_settings': True,
                            'can_access_logs': True,
                            'can_export_data': True,
                            'can_manage_maintenance': True
                        }
                    }
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Created admin profile for: {username}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ Admin profile already exists for: {username}')
                    )
                
                # Create initial system settings
                default_settings = [
                    {
                        'key': 'site_name',
                        'value': 'AURA - AI Personal Event Concierge',
                        'description': 'Main site title displayed to users',
                        'category': 'general'
                    },
                    {
                        'key': 'max_users_per_event',
                        'value': '500',
                        'description': 'Maximum number of users per event',
                        'category': 'events'
                    },
                    {
                        'key': 'chat_session_timeout',
                        'value': '3600',
                        'description': 'Chat session timeout in seconds',
                        'category': 'chat'
                    },
                    {
                        'key': 'enable_registration',
                        'value': 'true',
                        'description': 'Allow new user registrations',
                        'category': 'users'
                    },
                    {
                        'key': 'maintenance_message',
                        'value': 'AURA is currently under maintenance. We\'ll be back soon!',
                        'description': 'Message shown during maintenance mode',
                        'category': 'maintenance'
                    },
                    {
                        'key': 'ai_response_timeout',
                        'value': '10',
                        'description': 'AI response timeout in seconds',
                        'category': 'ai'
                    },
                    {
                        'key': 'max_concurrent_connections',
                        'value': '1000',
                        'description': 'Maximum concurrent WebSocket connections',
                        'category': 'performance'
                    },
                    {
                        'key': 'enable_analytics',
                        'value': 'true',
                        'description': 'Enable analytics data collection',
                        'category': 'analytics'
                    }
                ]
                
                settings_created = 0
                for setting_data in default_settings:
                    setting, created = SystemSettings.objects.get_or_create(
                        key=setting_data['key'],
                        defaults={
                            'value': setting_data['value'],
                            'description': setting_data['description'],
                            'category': setting_data['category'],
                            'created_by': user,
                            'is_active': True
                        }
                    )
                    
                    if created:
                        settings_created += 1
                
                if settings_created > 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Created {settings_created} system settings')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING('⚠️ System settings already exist')
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n🚀 AURA Admin Setup Complete!\n'
                        f'Username: {username}\n'
                        f'Password: {password}\n'
                        f'Admin Panel: http://localhost:8000/admin-panel/\n'
                        f'Django Admin: http://localhost:8000/admin/\n'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error during setup: {str(e)}')
            )