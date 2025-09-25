from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import random

from admin_panel.models import EventManagement, SystemLogs, Analytics
from attendees.models import AttendeeProfile
from chat.models import ChatSession, ChatMessage

class Command(BaseCommand):
    help = 'Populate the admin panel with sample data for testing'

    def handle(self, *args, **options):
        self.stdout.write('🔄 Creating sample data for AURA Admin Panel...')
        
        # Create sample users
        sample_users = [
            {'username': 'john_doe', 'email': 'john@example.com', 'first_name': 'John', 'last_name': 'Doe'},
            {'username': 'jane_smith', 'email': 'jane@example.com', 'first_name': 'Jane', 'last_name': 'Smith'},
            {'username': 'bob_wilson', 'email': 'bob@example.com', 'first_name': 'Bob', 'last_name': 'Wilson'},
            {'username': 'alice_brown', 'email': 'alice@example.com', 'first_name': 'Alice', 'last_name': 'Brown'},
            {'username': 'charlie_davis', 'email': 'charlie@example.com', 'first_name': 'Charlie', 'last_name': 'Davis'},
        ]
        
        users_created = 0
        for user_data in sample_users:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            
            if created:
                user.set_password('password123')
                user.save()
                users_created += 1
                
                # Create attendee profile
                AttendeeProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'job_title': random.choice(['Developer', 'Manager', 'Designer', 'Analyst', 'Engineer']),
                        'interests': random.choice([
                            'AI, Machine Learning, Technology',
                            'Web Development, Programming, Open Source',
                            'Data Science, Analytics, Visualization',
                            'Product Management, Strategy, Innovation',
                            'Design, UX, Creative Technologies'
                        ]),
                        'company': random.choice(['Tech Corp', 'Innovation Labs', 'Data Systems', 'Creative Agency', 'Startup Inc']),
                        'networking_preferences': random.choice(['open', 'selective', 'minimal']),
                        'first_time_attendee': random.choice([True, False])
                    }
                )
        
        self.stdout.write(f'✅ Created {users_created} sample users')
        
        # Create sample events
        sample_events = [
            {
                'title': 'Advanced React Development Workshop',
                'description': 'Deep dive into React hooks, context, and performance optimization techniques.',
                'status': 'published',
                'priority': 'high',
                'location': 'Tech Center Room A',
                'tags': 'React, JavaScript, Web Development, Workshop',
                'external_url': 'https://www.reactworkshop.com'
            },
            {
                'title': 'Machine Learning for Beginners',
                'description': 'Introduction to ML concepts, algorithms, and practical applications.',
                'status': 'published',
                'priority': 'medium',
                'location': 'Virtual Event',
                'tags': 'Machine Learning, AI, Data Science, Beginner',
                'external_url': 'https://www.mlbeginners.org'
            },
            {
                'title': 'DevOps Best Practices',
                'description': 'Learn about CI/CD, containerization, and infrastructure automation.',
                'status': 'draft',
                'priority': 'medium',
                'location': 'Conference Hall B',
                'tags': 'DevOps, CI/CD, Docker, Kubernetes, Automation',
                'external_url': 'https://www.devopsconf.com'
            },
            {
                'title': 'UX Design Thinking Session',
                'description': 'Collaborative session on user-centered design methodologies.',
                'status': 'published',
                'priority': 'low',
                'location': 'Design Studio',
                'tags': 'UX, Design, User Experience, Design Thinking',
                'external_url': 'https://www.uxdesign.io'
            },
            {
                'title': 'Blockchain and Cryptocurrency Summit',
                'description': 'Exploring the future of digital currencies and blockchain technology.',
                'status': 'published',
                'priority': 'high',
                'location': 'Main Auditorium',
                'tags': 'Blockchain, Cryptocurrency, DeFi, Web3',
                'external_url': 'https://www.blockchainsummit.com'
            }
        ]
        
        admin_user = User.objects.get(username='admin')
        events_created = 0
        
        for i, event_data in enumerate(sample_events):
            start_time = timezone.now() + timedelta(days=random.randint(1, 30), hours=random.randint(9, 17))
            end_time = start_time + timedelta(hours=random.randint(1, 4))
            
            event, created = EventManagement.objects.get_or_create(
                title=event_data['title'],
                defaults={
                    **event_data,
                    'start_datetime': start_time,
                    'end_datetime': end_time,
                    'max_attendees': random.randint(50, 500),
                    'current_attendees': random.randint(10, 100),
                    'created_by': admin_user
                }
            )
            
            if created:
                events_created += 1
        
        self.stdout.write(f'✅ Created {events_created} sample events')
        
        # Create sample system logs
        log_messages = [
            {'level': 'INFO', 'message': 'User login successful', 'module': 'authentication'},
            {'level': 'INFO', 'message': 'Event created successfully', 'module': 'events'},
            {'level': 'WARNING', 'message': 'High memory usage detected', 'module': 'system'},
            {'level': 'ERROR', 'message': 'Database connection timeout', 'module': 'database'},
            {'level': 'INFO', 'message': 'Chat session started', 'module': 'chat'},
            {'level': 'WARNING', 'message': 'Unusual login pattern detected', 'module': 'security'},
            {'level': 'INFO', 'message': 'System backup completed', 'module': 'maintenance'},
            {'level': 'ERROR', 'message': 'Failed to send notification', 'module': 'notifications'}
        ]
        
        logs_created = 0
        for i in range(20):  # Create 20 sample logs
            log_data = random.choice(log_messages)
            log = SystemLogs.objects.create(
                level=log_data['level'],
                message=f"{log_data['message']} - Sample entry #{i+1}",
                module=log_data['module'],
                user=random.choice([admin_user, None]),
                ip_address=f"192.168.1.{random.randint(100, 200)}",
                metadata={'sample': True, 'entry_id': i+1}
            )
            logs_created += 1
        
        self.stdout.write(f'✅ Created {logs_created} sample log entries')
        
        # Create sample analytics data
        analytics_created = 0
        metrics = [
            'daily_active_users',
            'new_registrations',
            'event_bookings',
            'chat_sessions',
            'page_views'
        ]
        
        for i in range(30):  # 30 days of data
            date = timezone.now().date() - timedelta(days=i)
            
            for metric in metrics:
                value = random.randint(10, 1000) if metric != 'daily_active_users' else random.randint(50, 500)
                
                analytics, created = Analytics.objects.get_or_create(
                    metric_name=metric,
                    metric_type='daily',
                    date_recorded=date,
                    defaults={
                        'metric_value': value,
                        'metadata': {'source': 'sample_data'}
                    }
                )
                
                if created:
                    analytics_created += 1
        
        self.stdout.write(f'✅ Created {analytics_created} analytics data points')
        
        # Create sample chat sessions
        all_users = User.objects.all()
        sessions_created = 0
        
        for user in all_users[:5]:  # Create sessions for first 5 users
            session, created = ChatSession.objects.get_or_create(
                user=user,
                session_id=f"session_{user.username}_{random.randint(1000, 9999)}",
                defaults={
                    'is_active': random.choice([True, False])
                }
            )
            
            if created:
                sessions_created += 1
                
                # Add some sample messages
                sample_messages = [
                    "Hello! Can you help me find events about AI?",
                    "What workshops are available this week?",
                    "I'm interested in web development sessions",
                    "Can you recommend networking events?",
                    "Show me beginner-friendly courses"
                ]
                
                for i, msg in enumerate(random.sample(sample_messages, 3)):
                    ChatMessage.objects.create(
                        session=session,
                        message_type='user',
                        content=msg,
                        metadata={'sample': True}
                    )
                    
                    # Bot response
                    ChatMessage.objects.create(
                        session=session,
                        message_type='bot',
                        content=f"I found several events that match your interests! Let me show you the best options.",
                        metadata={'sample': True, 'response_to': msg}
                    )
        
        self.stdout.write(f'✅ Created {sessions_created} sample chat sessions')
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n🎉 Sample data creation complete!\n'
                'Your admin panel now has:\n'
                f'• {users_created} sample users with profiles\n'
                f'• {events_created} sample events\n'
                f'• {logs_created} system log entries\n'
                f'• {analytics_created} analytics data points\n'
                f'• {sessions_created} chat sessions with messages\n\n'
                'Visit http://localhost:8001/admin-panel/ to explore!'
            )
        )