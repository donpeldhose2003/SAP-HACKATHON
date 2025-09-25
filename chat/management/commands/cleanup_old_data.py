from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from chat.models import ChatSession, ChatMessage, UserActivity

class Command(BaseCommand):
    help = 'Clean up old chat sessions and messages to maintain database performance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete sessions older than this many days (default: 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Find old sessions
        old_sessions = ChatSession.objects.filter(
            created_at__lt=cutoff_date,
            is_active=False
        )
        
        # Find associated messages
        old_messages = ChatMessage.objects.filter(
            session__in=old_sessions
        )
        
        # Find old activities
        old_activities = UserActivity.objects.filter(
            timestamp__lt=cutoff_date
        )
        
        session_count = old_sessions.count()
        message_count = old_messages.count()
        activity_count = old_activities.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN - No data will be deleted')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Found items older than {days} days:')
        )
        self.stdout.write(f'  - {session_count} chat sessions')
        self.stdout.write(f'  - {message_count} chat messages')
        self.stdout.write(f'  - {activity_count} user activities')
        
        if not dry_run:
            if session_count > 0 or message_count > 0 or activity_count > 0:
                # Delete old data
                deleted_messages = old_messages.delete()
                deleted_sessions = old_sessions.delete()
                deleted_activities = old_activities.delete()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully cleaned up:'
                        f'\n  - {deleted_messages[0]} messages'
                        f'\n  - {deleted_sessions[0]} sessions'
                        f'\n  - {deleted_activities[0]} activities'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('No old data found to clean up')
                )
        else:
            self.stdout.write(
                self.style.WARNING('Run without --dry-run to actually delete the data')
            )