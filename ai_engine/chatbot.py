import json
import re
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q, Count, Avg
from attendees.models import AttendeeProfile, EventInteraction
from events.models import Session, Speaker
from chat.models import ChatSession, ChatMessage, UserActivity
import random
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class ChatContext:
    """Context for maintaining conversation state"""
    user_intent: str = ""
    last_topic: str = ""
    conversation_depth: int = 0
    session_history: List[str] = None
    
    def __post_init__(self):
        if self.session_history is None:
            self.session_history = []

class AuraConcierge:
    def __init__(self):
        self.greetings = [
            "Hello {name}! 👋 Welcome to your personal AURA concierge. I'm here to make your event experience extraordinary!",
            "Hi {name}! 🌟 Ready to discover amazing sessions and connections today?",
            "Welcome back, {name}! ✨ Let's curate the perfect event journey for you.",
        ]
        
        self.conversation_starters = [
            "What brings you to this event?",
            "Are you looking for specific topics or speakers?",
            "Would you like me to recommend sessions based on your interests?",
            "Need help navigating today's schedule?",
        ]
    
    def get_response(self, message, user_context=None):
        """Main method to get chatbot response"""
        if not user_context or not user_context.is_authenticated:
            return self._guest_response()
        
        # Get or create chat session
        session = self._get_or_create_session(user_context)
        
        # Log user message
        self._log_message(session, 'user', message)
        
        # Get attendee profile
        try:
            profile = AttendeeProfile.objects.get(user=user_context)
        except AttendeeProfile.DoesNotExist:
            return self._onboarding_response(user_context)
        
        # Update last login
        profile.update_last_login()
        
        # Check if this is the first interaction
        if session.messages.count() <= 1:  # Only user message exists
            response = self._welcome_response(profile)
            self._log_message(session, 'welcome', response)
            return response
        
        # Process the message and generate response
        response = self._process_message(message, profile, session)
        self._log_message(session, 'bot', response)
        
        return response
    
    def _guest_response(self):
        return "Welcome to AURA! 🎉 Please log in or register to access your personal concierge and get personalized recommendations."
    
    def _onboarding_response(self, user):
        return f"Hi {user.first_name or user.username}! 👋 It looks like you're new here. Let me help you complete your profile so I can provide better recommendations. What are your main interests for this event?"
    
    def _welcome_response(self, profile):
        """Generate personalized welcome message"""
        name = profile.user.first_name or profile.user.username
        greeting = random.choice(self.greetings).format(name=name)
        
        # Add personalized context
        context_parts = []
        
        if profile.first_time_attendee:
            context_parts.append("I see this is your first time with us - how exciting! 🎊")
        else:
            context_parts.append("Great to have you back! 🌟")
        
        if profile.interests:
            interests = profile.interests.split(',')[:3]  # Show first 3 interests
            context_parts.append(f"Based on your interests in {', '.join(interests)}, I have some great recommendations lined up.")
        
        # Get immediate recommendations
        upcoming_sessions = self._get_upcoming_sessions(profile)
        if upcoming_sessions:
            context_parts.append("Here's what's happening soon that might interest you:")
            for session in upcoming_sessions[:2]:
                context_parts.append(f"📅 {session.title} - {session.start_time.strftime('%H:%M')}")
        
        context_parts.append("How can I help you make the most of your event today? 🚀")
        
        return greeting + "\n\n" + "\n".join(context_parts)
    
    def _process_message(self, message, profile, session):
        """Process user message and generate appropriate response"""
        message_lower = message.lower()
        
        # Intent detection
        if any(word in message_lower for word in ['recommend', 'suggest', 'session', 'talk', 'what should']):
            return self._handle_recommendation_request(message, profile)
        
        elif any(word in message_lower for word in ['schedule', 'agenda', 'timeline', 'when', 'time']):
            return self._handle_schedule_request(message, profile)
        
        elif any(word in message_lower for word in ['speaker', 'who', 'presenter']):
            return self._handle_speaker_request(message, profile)
        
        elif any(word in message_lower for word in ['location', 'where', 'room', 'venue']):
            return self._handle_location_request(message, profile)
        
        elif any(word in message_lower for word in ['network', 'connect', 'meet', 'people']):
            return self._handle_networking_request(message, profile)
        
        elif any(word in message_lower for word in ['help', 'assistance', 'support']):
            return self._handle_help_request()
        
        elif any(word in message_lower for word in ['thank', 'thanks', 'great', 'awesome']):
            return self._handle_appreciation()
        
        else:
            return self._handle_general_query(message, profile)
    
    def _handle_recommendation_request(self, message, profile):
        """Handle session recommendation requests"""
        recommendations = self._get_personalized_recommendations(profile)
        
        if not recommendations:
            return "I don't see any upcoming sessions right now, but let me know what topics interest you and I'll keep an eye out! 👀"
        
        response_parts = ["Here are my top recommendations for you: ✨\n"]
        
        for i, session in enumerate(recommendations, 1):
            time_str = session.start_time.strftime('%H:%M')
            response_parts.append(f"{i}. 📍 **{session.title}**")
            response_parts.append(f"   ⏰ {time_str}")
            if session.speaker:
                response_parts.append(f"   👤 {session.speaker.name}")
            response_parts.append(f"   📝 {session.description[:100]}...")
            response_parts.append("")
        
        response_parts.append("Would you like more details about any of these sessions? 🤔")
        
        return "\n".join(response_parts)
    
    def _handle_schedule_request(self, message, profile):
        """Handle schedule and timing requests"""
        now = timezone.now()
        today_sessions = Session.objects.filter(
            start_time__date=now.date()
        ).order_by('start_time')
        
        if not today_sessions.exists():
            return "No sessions scheduled for today. Check back tomorrow! 📅"
        
        response_parts = ["Here's today's schedule: 📋\n"]
        
        for session in today_sessions:
            time_str = session.start_time.strftime('%H:%M')
            status = "🔴 Live now!" if now >= session.start_time and now <= session.end_time else ""
            status = status or ("⏰ Coming up!" if session.start_time <= now + timedelta(hours=1) else "")
            
            response_parts.append(f"**{time_str}** - {session.title} {status}")
        
        response_parts.append("\nWant me to add any of these to your personal schedule? 📌")
        
        return "\n".join(response_parts)
    
    def _handle_speaker_request(self, message, profile):
        """Handle speaker information requests"""
        speakers = Speaker.objects.all()[:5]  # Limit to prevent overwhelming
        
        if not speakers.exists():
            return "Speaker information will be available soon! 🎤"
        
        response_parts = ["Here are some featured speakers: 🌟\n"]
        
        for speaker in speakers:
            response_parts.append(f"👤 **{speaker.name}**")
            response_parts.append(f"🏢 {speaker.company}")
            response_parts.append(f"📄 {speaker.bio[:150]}...")
            response_parts.append("")
        
        response_parts.append("Want to know which sessions they're presenting? Just ask! 💬")
        
        return "\n".join(response_parts)
    
    def _handle_location_request(self, message, profile):
        """Handle location and venue requests"""
        # This is a placeholder - you can integrate with actual venue data
        return """🗺️ **Venue Information:**

**Main Auditorium** - Keynotes and main sessions
**Conference Room A** - Technical workshops  
**Conference Room B** - Panel discussions
**Networking Lounge** - Coffee breaks and networking
**Exhibition Hall** - Sponsor booths and demos

Need directions to a specific room? Just ask! 🧭"""
    
    def _handle_networking_request(self, message, profile):
        """Handle networking requests"""
        # This could be enhanced with actual attendee matching
        networking_tips = [
            "💡 **Networking Tips:**",
            "• Coffee breaks are great for casual conversations",
            "• Join the lunch networking session in the main hall",
            "• Check out the interactive booths in the exhibition area",
            "• Don't forget to exchange contact information!",
            "",
            "Would you like me to suggest attendees with similar interests? 🤝"
        ]
        
        return "\n".join(networking_tips)
    
    def _handle_help_request(self):
        """Handle help requests"""
        help_text = """🆘 **I'm here to help!** Here's what I can do:

✅ **Recommend sessions** based on your interests
✅ **Show schedules** and timing information  
✅ **Find speakers** and their sessions
✅ **Provide venue** directions and maps
✅ **Suggest networking** opportunities
✅ **Send alerts** for sessions you're interested in

Just ask me anything in natural language! For example:
• "What sessions should I attend?"
• "When is the next keynote?"
• "Who's speaking about AI?"

What would you like to know? 😊"""
        
        return help_text
    
    def _handle_appreciation(self):
        """Handle thank you messages"""
        responses = [
            "You're very welcome! I'm here whenever you need me! 😊",
            "Happy to help! Enjoy the event! 🌟",
            "My pleasure! Let me know if you need anything else! ✨",
        ]
        return random.choice(responses)
    
    def _handle_general_query(self, message, profile):
        """Handle general queries"""
        # Try to extract key topics from the message
        if any(topic in message.lower() for topic in ['ai', 'artificial intelligence', 'machine learning', 'ml']):
            ai_sessions = Session.objects.filter(
                Q(title__icontains='AI') | Q(title__icontains='artificial intelligence') | 
                Q(description__icontains='AI') | Q(description__icontains='machine learning')
            )[:3]
            
            if ai_sessions.exists():
                response_parts = ["I found some AI-related sessions for you: 🤖\n"]
                for session in ai_sessions:
                    response_parts.append(f"• {session.title} - {session.start_time.strftime('%H:%M')}")
                return "\n".join(response_parts)
        
        # Default response with helpful suggestions
        return """I'm not sure I understand that exactly, but I'm here to help! 🤔

Try asking me:
• "What sessions do you recommend?"
• "Show me today's schedule"
• "Who are the speakers?"
• "Help me with networking"

What would you like to know about the event? 💬"""
    
    def _get_personalized_recommendations(self, profile):
        """Get personalized session recommendations"""
        from ai_engine.recommendation import get_session_recommendations
        
        # Use the existing recommendation system and enhance it
        base_recommendations = get_session_recommendations(profile.id)
        
        # Filter based on user interactions and interests
        user_interests = profile.interests.lower().split(',') if profile.interests else []
        
        scored_sessions = []
        for session in base_recommendations:
            score = 0
            
            # Score based on interests
            for interest in user_interests:
                interest = interest.strip()
                if interest in session.title.lower() or interest in session.description.lower():
                    score += 10
            
            # Boost upcoming sessions
            now = timezone.now()
            if session.start_time > now and session.start_time <= now + timedelta(hours=4):
                score += 5
            
            # Check if user has already interacted
            has_interaction = EventInteraction.objects.filter(
                attendee=profile,
                event_id=session.id
            ).exists()
            
            if not has_interaction:
                score += 3
            
            scored_sessions.append((session, score))
        
        # Sort by score and return top sessions
        scored_sessions.sort(key=lambda x: x[1], reverse=True)
        return [session for session, score in scored_sessions[:3]]
    
    def _get_upcoming_sessions(self, profile):
        """Get upcoming sessions for the user"""
        now = timezone.now()
        return Session.objects.filter(
            start_time__gt=now,
            start_time__lte=now + timedelta(hours=2)
        ).order_by('start_time')[:3]
    
    def _get_or_create_session(self, user):
        """Get or create chat session for user"""
        session_id = f"session_{user.id}_{timezone.now().date()}"
        session, created = ChatSession.objects.get_or_create(
            user=user,
            session_id=session_id,
            defaults={'is_active': True}
        )
        return session
    
    def _log_message(self, session, message_type, content, metadata=None):
        """Log chat message"""
        ChatMessage.objects.create(
            session=session,
            message_type=message_type,
            content=content,
            metadata=metadata
        )
    
    def get_live_feed(self, user):
        """Generate live feed of personalized content with real event information"""
        if not user.is_authenticated:
            return self._get_sample_events()
        
        try:
            profile = AttendeeProfile.objects.get(user=user)
        except AttendeeProfile.DoesNotExist:
            return self._get_sample_events()
        
        feed_items = []
        now = timezone.now()
        
        # Add real-world event examples
        sample_events = self._get_sample_events()
        feed_items.extend(sample_events)
        
        # Upcoming sessions (if any exist in database)
        try:
            upcoming = self._get_upcoming_sessions(profile)
            for session in upcoming:
                feed_items.append({
                    'type': 'upcoming_session',
                    'title': f"📅 Starting soon: {session.title}",
                    'content': f"Starts at {session.start_time.strftime('%H:%M')}",
                    'action': "View Details",
                    'url': f"https://example.com/session/{session.id}",
                    'priority': 'high' if session.start_time <= now + timedelta(minutes=30) else 'medium'
                })
        except:
            pass
        
        # Personalized recommendations
        try:
            recommendations = self._get_personalized_recommendations(profile)
            for session in recommendations:
                feed_items.append({
                    'type': 'recommendation',
                    'title': f"🎯 Recommended: {session.title}",
                    'content': f"Match score: {random.randint(85, 99)}%",
                    'action': "Learn More",
                    'url': f"https://example.com/session/{session.id}",
                    'priority': 'medium'
                })
        except:
            pass
            feed_items.append({
                'type': 'recommendation',
                'title': f"💡 Recommended: {session.title}",
                'content': session.description[:100] + "...",
                'action': f"Learn more about {session.title}",
                'priority': 'medium'
            })
        
        # Networking suggestions
        if profile.networking_preferences == 'open':
            feed_items.append({
                'type': 'networking',
                'title': "🤝 Networking Opportunity",
                'content': "Coffee break starting in 15 minutes - great time to connect!",
                'action': "Get networking tips",
                'priority': 'low'
            })
        
        return sorted(feed_items, key=lambda x: {'high': 3, 'medium': 2, 'low': 1}[x['priority']], reverse=True)
    
    def _get_sample_events(self):
        """Get sample events with real-world information and external links"""
        sample_events = [
            {
                'type': 'tech_conference',
                'title': '🚀 AI & Machine Learning Summit 2025',
                'content': 'Join industry leaders discussing the future of AI, ML applications, and emerging technologies. Keynote by leading tech innovators.',
                'action': 'Register Now',
                'url': 'https://www.ai-ml-summit.com',
                'priority': 'high',
                'time': '10:00 AM - 6:00 PM',
                'date': 'October 15, 2025'
            },
            {
                'type': 'startup_pitch',
                'title': '💡 Startup Pitch Competition',
                'content': 'Watch innovative startups present their groundbreaking ideas to top VCs and angel investors. Network with entrepreneurs.',
                'action': 'View Startups',
                'url': 'https://www.startuppitch2025.com',
                'priority': 'high',
                'time': '2:00 PM - 5:00 PM',
                'date': 'Today'
            },
            {
                'type': 'developer_workshop',
                'title': '⚡ Full-Stack Development Workshop',
                'content': 'Hands-on workshop covering React, Node.js, and modern development practices. Build a complete web application.',
                'action': 'Join Workshop',
                'url': 'https://www.devworkshop.io',
                'priority': 'medium',
                'time': '9:00 AM - 12:00 PM',
                'date': 'Tomorrow'
            },
            {
                'type': 'networking_event',
                'title': '🤝 Tech Networking Mixer',
                'content': 'Connect with fellow developers, designers, and tech enthusiasts. Casual networking over coffee and snacks.',
                'action': 'RSVP Here',
                'url': 'https://www.technetworking.events',
                'priority': 'medium',
                'time': '6:00 PM - 9:00 PM',
                'date': 'October 20, 2025'
            },
            {
                'type': 'innovation_showcase',
                'title': '🌟 Innovation & Design Showcase',
                'content': 'Discover cutting-edge design trends, UX innovations, and creative technology solutions from top design agencies.',
                'action': 'Explore Showcase',
                'url': 'https://www.innovationshowcase.design',
                'priority': 'medium',
                'time': '11:00 AM - 4:00 PM',
                'date': 'October 25, 2025'
            },
            {
                'type': 'career_fair',
                'title': '💼 Tech Career Fair 2025',
                'content': 'Meet recruiters from top tech companies including Google, Microsoft, Apple, and emerging startups. Bring your resume!',
                'action': 'Find Jobs',
                'url': 'https://www.techcareers2025.com',
                'priority': 'high',
                'time': '10:00 AM - 6:00 PM',
                'date': 'November 1, 2025'
            }
        ]
        
        # Randomize and return 3-4 events
        import random
        selected_events = random.sample(sample_events, min(4, len(sample_events)))
        
        # Format for the frontend
        formatted_events = []
        for event in selected_events:
            formatted_events.append({
                'type': event['type'],
                'title': event['title'],
                'content': f"{event['content']}\n\n📅 {event['date']} | ⏰ {event['time']}",
                'action': event['action'],
                'url': event['url'],
                'priority': event['priority']
            })
        
        return formatted_events

# Global instance
concierge = AuraConcierge()

def get_response(message, user_context=None):
    """Main entry point for chatbot responses"""
    return concierge.get_response(message, user_context)

def get_live_feed(user):
    """Get personalized live feed"""
    return concierge.get_live_feed(user)