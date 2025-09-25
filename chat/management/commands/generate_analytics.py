from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from chat.models import ChatSession, ChatMessage, UserActivity
from django.db.models import Count, Avg
import json

class Command(BaseCommand):
    help = 'Generate analytics report for AURA chatbot usage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to analyze (default: 7)',
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path for JSON report',
        )

    def handle(self, *args, **options):
        days = options['days']
        start_date = timezone.now() - timedelta(days=days)
        
        self.stdout.write(
            self.style.SUCCESS(f'Generating analytics report for the last {days} days...')
        )

        # Basic metrics
        total_sessions = ChatSession.objects.filter(created_at__gte=start_date).count()
        active_sessions = ChatSession.objects.filter(
            created_at__gte=start_date, 
            is_active=True
        ).count()
        total_messages = ChatMessage.objects.filter(timestamp__gte=start_date).count()
        
        # User engagement
        unique_users = ChatSession.objects.filter(
            created_at__gte=start_date
        ).values('user').distinct().count()
        
        # Message type breakdown
        message_stats = ChatMessage.objects.filter(
            timestamp__gte=start_date
        ).values('message_type').annotate(
            count=Count('id')
        ).order_by('message_type')
        
        # Average session length (calculate in Python for better compatibility)
        sessions_with_duration = ChatSession.objects.filter(
            created_at__gte=start_date,
            last_activity__isnull=False
        ).select_related('user')
        
        total_duration = 0
        session_count = 0
        for session in sessions_with_duration:
            if session.last_activity and session.created_at:
                duration = session.last_activity - session.created_at
                total_duration += duration.total_seconds()
                session_count += 1
        
        avg_session_duration = (total_duration / session_count / 3600) if session_count > 0 else 0
        
        # Most active users
        top_users = ChatSession.objects.filter(
            created_at__gte=start_date
        ).values('user__username').annotate(
            session_count=Count('id'),
            message_count=Count('messages')
        ).order_by('-session_count')[:10]
        
        # Activity patterns
        activity_stats = UserActivity.objects.filter(
            timestamp__gte=start_date
        ).values('activity_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Generate report
        report = {
            'period': f'{days} days',
            'generated_at': timezone.now().isoformat(),
            'overview': {
                'total_sessions': total_sessions,
                'active_sessions': active_sessions,
                'total_messages': total_messages,
                'unique_users': unique_users,
                'avg_session_duration_hours': round(avg_session_duration, 2)
            },
            'message_breakdown': {
                item['message_type']: item['count'] for item in message_stats
            },
            'top_users': list(top_users),
            'activity_patterns': {
                item['activity_type']: item['count'] for item in activity_stats
            }
        }
        
        # Display report
        self.stdout.write(self.style.SUCCESS('\n=== AURA Analytics Report ==='))
        self.stdout.write(f"Period: {report['period']}")
        self.stdout.write(f"Generated: {report['generated_at']}")
        
        self.stdout.write(self.style.WARNING('\n--- Overview ---'))
        for key, value in report['overview'].items():
            self.stdout.write(f"{key.replace('_', ' ').title()}: {value}")
        
        self.stdout.write(self.style.WARNING('\n--- Message Types ---'))
        for msg_type, count in report['message_breakdown'].items():
            self.stdout.write(f"{msg_type}: {count}")
        
        self.stdout.write(self.style.WARNING('\n--- Top 5 Users ---'))
        for user in report['top_users'][:5]:
            self.stdout.write(
                f"{user['user__username']}: {user['session_count']} sessions, "
                f"{user['message_count']} messages"
            )
        
        # Save to file if requested
        if options['output']:
            with open(options['output'], 'w') as f:
                json.dump(report, f, indent=2)
            self.stdout.write(
                self.style.SUCCESS(f'\nReport saved to {options["output"]}')
            )
        
        self.stdout.write(self.style.SUCCESS('\nAnalytics report generated successfully!'))