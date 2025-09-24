from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from events.models import Speaker, Session

class Command(BaseCommand):
    help = 'Populate database with sample events and speakers'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating sample speakers...')
        
        # Create sample speakers
        speakers_data = [
            {
                'name': 'Dr. Sarah Chen',
                'bio': 'Leading AI researcher and author of "The Future of Machine Learning". PhD from MIT, currently Director of AI at TechCorp.',
                'company': 'TechCorp AI Labs'
            },
            {
                'name': 'Michael Rodriguez',
                'bio': 'Digital transformation expert with 15+ years experience. Former CTO at StartupX, now consulting for Fortune 500 companies.',
                'company': 'Rodriguez Consulting'
            },
            {
                'name': 'Prof. Emma Johnson',
                'bio': 'Professor of Computer Science at Stanford University. Expert in human-computer interaction and user experience design.',
                'company': 'Stanford University'
            },
            {
                'name': 'David Kim',
                'bio': 'Blockchain pioneer and cryptocurrency entrepreneur. Founded three successful startups in the Web3 space.',
                'company': 'BlockChain Innovations'
            },
            {
                'name': 'Lisa Thompson',
                'bio': 'Cybersecurity expert and ethical hacker. Former NSA analyst, now heads security at CloudSecure.',
                'company': 'CloudSecure Inc.'
            }
        ]
        
        speakers = []
        for speaker_data in speakers_data:
            speaker, created = Speaker.objects.get_or_create(
                name=speaker_data['name'],
                defaults=speaker_data
            )
            speakers.append(speaker)
            if created:
                self.stdout.write(f'Created speaker: {speaker.name}')
        
        self.stdout.write('Creating sample sessions...')
        
        # Create sample sessions
        now = timezone.now()
        today = now.replace(hour=9, minute=0, second=0, microsecond=0)
        
        sessions_data = [
            {
                'title': 'Keynote: The Future of AI in Business',
                'description': 'Join Dr. Sarah Chen as she explores how artificial intelligence is transforming modern business practices and what leaders need to know to stay competitive.',
                'start_time': today,
                'end_time': today + timedelta(hours=1),
                'speaker': speakers[0]
            },
            {
                'title': 'Digital Transformation Workshop',
                'description': 'A hands-on workshop covering practical strategies for implementing digital transformation in your organization. Includes case studies and interactive exercises.',
                'start_time': today + timedelta(hours=1, minutes=30),
                'end_time': today + timedelta(hours=3),
                'speaker': speakers[1]
            },
            {
                'title': 'User Experience Design Principles',
                'description': 'Learn the fundamental principles of UX design and how to create intuitive, user-friendly interfaces that delight customers.',
                'start_time': today + timedelta(hours=3, minutes=30),
                'end_time': today + timedelta(hours=4, minutes=30),
                'speaker': speakers[2]
            },
            {
                'title': 'Blockchain and Web3: Beyond the Hype',
                'description': 'Cutting through the noise to understand real-world applications of blockchain technology and decentralized systems.',
                'start_time': today + timedelta(hours=5),
                'end_time': today + timedelta(hours=6),
                'speaker': speakers[3]
            },
            {
                'title': 'Cybersecurity Best Practices',
                'description': 'Essential security practices every organization needs to implement to protect against modern cyber threats.',
                'start_time': today + timedelta(hours=6, minutes=30),
                'end_time': today + timedelta(hours=7, minutes=30),
                'speaker': speakers[4]
            },
            {
                'title': 'AI Ethics and Responsible Development',
                'description': 'Exploring the ethical implications of AI development and frameworks for responsible AI implementation.',
                'start_time': today + timedelta(days=1, hours=1),
                'end_time': today + timedelta(days=1, hours=2),
                'speaker': speakers[0]
            },
            {
                'title': 'Panel: Future of Work',
                'description': 'Industry leaders discuss how technology is reshaping the workplace and what skills will be most valuable in the coming decade.',
                'start_time': today + timedelta(days=1, hours=2, minutes=30),
                'end_time': today + timedelta(days=1, hours=3, minutes=30),
                'speaker': None  # Panel session
            },
            {
                'title': 'Networking Lunch: Innovation Showcase',
                'description': 'Connect with fellow attendees while exploring innovative projects and startups. Light lunch will be provided.',
                'start_time': today + timedelta(days=1, hours=4),
                'end_time': today + timedelta(days=1, hours=5),
                'speaker': None
            }
        ]
        
        for session_data in sessions_data:
            session, created = Session.objects.get_or_create(
                title=session_data['title'],
                defaults=session_data
            )
            if created:
                self.stdout.write(f'Created session: {session.title}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(speakers)} speakers and {len(sessions_data)} sessions'
            )
        )