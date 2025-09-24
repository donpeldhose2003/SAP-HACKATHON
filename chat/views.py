from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from attendees.models import AttendeeProfile, EventInteraction
from chat.models import ChatSession, UserActivity
from ai_engine.chatbot import get_live_feed
import json

@login_required
def dashboard(request):
    """Main dashboard view with chatbot interface"""
    try:
        profile = AttendeeProfile.objects.get(user=request.user)
    except AttendeeProfile.DoesNotExist:
        # Redirect to profile creation if not exists
        return redirect('chat:create_profile')
    
    # Get initial live feed
    live_feed = get_live_feed(request.user)
    
    context = {
        'user': request.user,
        'profile': profile,
        'live_feed': live_feed,
    }
    
    return render(request, 'index.html', context)

def home(request):
    """Home page that redirects based on authentication status"""
    if request.user.is_authenticated:
        return redirect('chat:dashboard')
    else:
        return render(request, 'home.html')

def user_login(request):
    """Handle user login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            # Update last login in profile
            try:
                profile = AttendeeProfile.objects.get(user=user)
                profile.update_last_login()
            except AttendeeProfile.DoesNotExist:
                pass
            
            return redirect('chat:dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')

def user_logout(request):
    """Handle user logout"""
    logout(request)
    return redirect('chat:home')

def register(request):
    """Handle user registration"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        
        # Validation
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'register.html')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Redirect to profile creation
        login(request, user)
        return redirect('chat:create_profile')
    
    return render(request, 'register.html')

@login_required
def create_profile(request):
    """Create attendee profile"""
    if request.method == 'POST':
        job_title = request.POST.get('job_title', '')
        company = request.POST.get('company', '')
        interests = request.POST.get('interests', '')
        bio = request.POST.get('bio', '')
        networking_preferences = request.POST.get('networking_preferences', 'open')
        first_time_attendee = request.POST.get('first_time_attendee') == 'on'
        
        profile, created = AttendeeProfile.objects.get_or_create(
            user=request.user,
            defaults={
                'job_title': job_title,
                'company': company,
                'interests': interests,
                'bio': bio,
                'networking_preferences': networking_preferences,
                'first_time_attendee': first_time_attendee,
            }
        )
        
        if not created:
            # Update existing profile
            profile.job_title = job_title
            profile.company = company
            profile.interests = interests
            profile.bio = bio
            profile.networking_preferences = networking_preferences
            profile.first_time_attendee = first_time_attendee
            profile.save()
        
        messages.success(request, 'Profile created successfully!')
        return redirect('chat:dashboard')
    
    return render(request, 'create_profile.html')

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def log_activity(request):
    """API endpoint to log user activities"""
    try:
        data = json.loads(request.body)
        activity_type = data.get('activity_type')
        activity_data = data.get('activity_data', {})
        
        UserActivity.objects.create(
            user=request.user,
            activity_type=activity_type,
            activity_data=activity_data
        )
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
def get_feed_api(request):
    """API endpoint to get updated live feed"""
    live_feed = get_live_feed(request.user)
    return JsonResponse({'live_feed': live_feed})

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def event_interaction(request):
    """Log event interactions (view, register, bookmark, etc.)"""
    try:
        data = json.loads(request.body)
        event_id = data.get('event_id')
        interaction_type = data.get('interaction_type')
        rating = data.get('rating')
        notes = data.get('notes', '')
        
        profile = AttendeeProfile.objects.get(user=request.user)
        
        interaction, created = EventInteraction.objects.get_or_create(
            attendee=profile,
            event_id=event_id,
            interaction_type=interaction_type,
            defaults={
                'rating': rating,
                'notes': notes
            }
        )
        
        if not created:
            # Update existing interaction
            if rating:
                interaction.rating = rating
            if notes:
                interaction.notes = notes
            interaction.save()
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

def about(request):
    """About page"""
    return render(request, 'about.html')

def features(request):
    """Features page"""
    return render(request, 'features.html')

def test_websocket(request):
    """WebSocket test page"""
    return render(request, 'test_websocket.html')
