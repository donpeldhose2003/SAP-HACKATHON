from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime, timedelta
import csv

from .models import (
    AdminProfile, SystemSettings, EventManagement, UserManagement,
    SystemLogs, Analytics, NotificationTemplate, MaintenanceMode
)
from attendees.models import AttendeeProfile, EventInteraction
from chat.models import ChatSession, ChatMessage
from events.models import Session

def is_admin_user(user):
    """Check if user has admin privileges"""
    try:
        admin_profile = AdminProfile.objects.get(user=user)
        return admin_profile.is_active_admin
    except AdminProfile.DoesNotExist:
        return user.is_staff or user.is_superuser

def admin_login(request):
    """Admin login page"""
    if request.user.is_authenticated and is_admin_user(request.user):
        return redirect('admin_panel:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None and is_admin_user(user):
            login(request, user)
            
            # Update admin profile last login
            try:
                admin_profile = AdminProfile.objects.get(user=user)
                admin_profile.update_last_login()
            except AdminProfile.DoesNotExist:
                pass
            
            next_url = request.GET.get('next', 'admin_panel:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions.')
    
    return render(request, 'admin_panel/login.html')

def admin_logout(request):
    """Admin logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('admin_panel:login')

@login_required
@user_passes_test(is_admin_user)
def admin_dashboard(request):
    """Main admin dashboard with key metrics"""
    
    # Get current admin profile
    try:
        admin_profile = AdminProfile.objects.get(user=request.user)
        admin_profile.update_last_login()
    except AdminProfile.DoesNotExist:
        admin_profile = None
    
    # Calculate key metrics
    total_users = User.objects.count()
    active_users_today = User.objects.filter(last_login__date=timezone.now().date()).count()
    total_events = EventManagement.objects.count()
    active_events = EventManagement.objects.filter(status='published').count()
    total_chat_sessions = ChatSession.objects.count()
    active_sessions = ChatSession.objects.filter(is_active=True).count()
    
    # Recent activities
    recent_logs = SystemLogs.objects.all()[:10]
    recent_registrations = User.objects.filter(date_joined__gte=timezone.now() - timedelta(days=7)).count()
    
    # System health
    maintenance_mode = MaintenanceMode.objects.filter(is_active=True).first()
    
    # User engagement metrics
    top_events = EventManagement.objects.annotate(
        interaction_count=Count('id')
    ).order_by('-interaction_count')[:5]
    
    context = {
        'admin_profile': admin_profile,
        'metrics': {
            'total_users': total_users,
            'active_users_today': active_users_today,
            'total_events': total_events,
            'active_events': active_events,
            'total_chat_sessions': total_chat_sessions,
            'active_sessions': active_sessions,
            'recent_registrations': recent_registrations,
        },
        'recent_logs': recent_logs,
        'maintenance_mode': maintenance_mode,
        'top_events': top_events,
    }
    
    return render(request, 'admin_panel/dashboard.html', context)

@login_required
@user_passes_test(is_admin_user)
def user_management(request):
    """User management interface"""
    
    search_query = request.GET.get('search', '')
    filter_status = request.GET.get('status', 'all')
    
    users = User.objects.select_related('attendeeprofile').all()
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    if filter_status == 'active':
        users = users.filter(is_active=True)
    elif filter_status == 'suspended':
        try:
            suspended_user_ids = UserManagement.objects.filter(is_suspended=True).values_list('user_id', flat=True)
            users = users.filter(id__in=suspended_user_ids)
        except:
            pass
    
    paginator = Paginator(users, 25)
    page_number = request.GET.get('page')
    users_page = paginator.get_page(page_number)
    
    context = {
        'users': users_page,
        'search_query': search_query,
        'filter_status': filter_status,
    }
    
    return render(request, 'admin_panel/user_management.html', context)

@login_required
@user_passes_test(is_admin_user)
def event_management(request):
    """Event management interface"""
    
    events = EventManagement.objects.all().order_by('-created_at')
    
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'all')
    
    if search_query:
        events = events.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(tags__icontains=search_query)
        )
    
    if status_filter != 'all':
        events = events.filter(status=status_filter)
    
    paginator = Paginator(events, 20)
    page_number = request.GET.get('page')
    events_page = paginator.get_page(page_number)
    
    context = {
        'events': events_page,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': EventManagement.STATUS_CHOICES,
    }
    
    return render(request, 'admin_panel/event_management.html', context)

@login_required
@user_passes_test(is_admin_user)
def system_settings(request):
    """System settings management"""
    
    if request.method == 'POST':
        key = request.POST.get('key')
        value = request.POST.get('value')
        description = request.POST.get('description', '')
        category = request.POST.get('category', 'general')
        
        setting, created = SystemSettings.objects.get_or_create(
            key=key,
            defaults={
                'value': value,
                'description': description,
                'category': category,
                'created_by': request.user
            }
        )
        
        if not created:
            setting.value = value
            setting.description = description
            setting.category = category
            setting.save()
        
        messages.success(request, f"Setting '{key}' {'created' if created else 'updated'} successfully.")
        return redirect('admin_panel:system_settings')
    
    settings = SystemSettings.objects.all().order_by('category', 'key')
    categories = settings.values_list('category', flat=True).distinct()
    
    context = {
        'settings': settings,
        'categories': categories,
    }
    
    return render(request, 'admin_panel/system_settings.html', context)

@login_required
@user_passes_test(is_admin_user)
def analytics_dashboard(request):
    """Analytics and reporting dashboard"""
    
    # Date range filter
    days = int(request.GET.get('days', 30))
    start_date = timezone.now().date() - timedelta(days=days)
    
    # User analytics
    daily_registrations = []
    daily_logins = []
    
    for i in range(days):
        date = start_date + timedelta(days=i)
        registrations = User.objects.filter(date_joined__date=date).count()
        logins = User.objects.filter(last_login__date=date).count()
        
        daily_registrations.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': registrations
        })
        daily_logins.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': logins
        })
    
    # Event analytics
    event_stats = EventManagement.objects.values('status').annotate(count=Count('id'))
    
    # Chat analytics
    chat_stats = ChatMessage.objects.filter(
        timestamp__date__gte=start_date
    ).values('message_type').annotate(count=Count('id'))
    
    # Top users by activity
    active_users = User.objects.annotate(
        message_count=Count('chatsession__messages'),
        session_count=Count('chatsession')
    ).order_by('-message_count')[:10]
    
    context = {
        'daily_registrations': daily_registrations,
        'daily_logins': daily_logins,
        'event_stats': list(event_stats),
        'chat_stats': list(chat_stats),
        'active_users': active_users,
        'days': days,
    }
    
    return render(request, 'admin_panel/analytics.html', context)

@login_required
@user_passes_test(is_admin_user)
def system_logs(request):
    """System logs viewer"""
    
    level_filter = request.GET.get('level', 'all')
    search_query = request.GET.get('search', '')
    
    logs = SystemLogs.objects.all()
    
    if level_filter != 'all':
        logs = logs.filter(level=level_filter)
    
    if search_query:
        logs = logs.filter(
            Q(message__icontains=search_query) |
            Q(module__icontains=search_query)
        )
    
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    logs_page = paginator.get_page(page_number)
    
    context = {
        'logs': logs_page,
        'level_filter': level_filter,
        'search_query': search_query,
        'log_levels': SystemLogs.LOG_LEVELS,
    }
    
    return render(request, 'admin_panel/system_logs.html', context)

@login_required
@user_passes_test(is_admin_user)
@require_http_methods(["POST"])
def suspend_user(request, user_id):
    """Suspend or unsuspend a user"""
    
    user = get_object_or_404(User, id=user_id)
    reason = request.POST.get('reason', '')
    
    user_mgmt, created = UserManagement.objects.get_or_create(user=user)
    
    if user_mgmt.is_suspended:
        user_mgmt.is_suspended = False
        user_mgmt.suspension_date = None
        user_mgmt.suspension_reason = ''
        user.is_active = True
        action = 'unsuspended'
    else:
        user_mgmt.is_suspended = True
        user_mgmt.suspension_date = timezone.now()
        user_mgmt.suspension_reason = reason
        user.is_active = False
        action = 'suspended'
    
    user_mgmt.save()
    user.save()
    
    # Log the action
    SystemLogs.objects.create(
        level='INFO',
        message=f"User {user.username} {action} by {request.user.username}",
        module='admin_panel',
        user=request.user,
        metadata={'target_user': user.username, 'action': action, 'reason': reason}
    )
    
    return JsonResponse({'success': True, 'action': action})

@login_required
@user_passes_test(is_admin_user)
def maintenance_mode(request):
    """Toggle maintenance mode"""
    
    if request.method == 'POST':
        is_active = request.POST.get('is_active') == 'true'
        message = request.POST.get('message', 'System is under maintenance.')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        
        # Parse datetime strings
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        except:
            start_dt = timezone.now()
            end_dt = timezone.now() + timedelta(hours=1)
        
        maintenance, created = MaintenanceMode.objects.get_or_create(
            defaults={
                'is_active': is_active,
                'message': message,
                'start_time': start_dt,
                'end_time': end_dt,
                'created_by': request.user
            }
        )
        
        if not created:
            maintenance.is_active = is_active
            maintenance.message = message
            maintenance.start_time = start_dt
            maintenance.end_time = end_dt
            maintenance.save()
        
        # Log the action
        SystemLogs.objects.create(
            level='WARNING',
            message=f"Maintenance mode {'activated' if is_active else 'deactivated'} by {request.user.username}",
            module='admin_panel',
            user=request.user,
            metadata={'maintenance_active': is_active, 'message': message}
        )
        
        return JsonResponse({'success': True, 'is_active': is_active})
    
    maintenance = MaintenanceMode.objects.first()
    
    context = {
        'maintenance': maintenance,
    }
    
    return render(request, 'admin_panel/maintenance_mode.html', context)

@login_required
@user_passes_test(is_admin_user)
def export_data(request):
    """Export system data as CSV"""
    
    export_type = request.GET.get('type', 'users')
    
    response = HttpResponse(content_type='text/csv')
    
    if export_type == 'users':
        response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
        writer = csv.writer(response)
        writer.writerow(['Username', 'Email', 'First Name', 'Last Name', 'Date Joined', 'Last Login', 'Is Active'])
        
        users = User.objects.all()
        for user in users:
            writer.writerow([
                user.username,
                user.email,
                user.first_name,
                user.last_name,
                user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '',
                user.is_active
            ])
    
    elif export_type == 'events':
        response['Content-Disposition'] = 'attachment; filename="events_export.csv"'
        writer = csv.writer(response)
        writer.writerow(['Title', 'Status', 'Start Date', 'End Date', 'Attendees', 'Max Attendees', 'Created By'])
        
        events = EventManagement.objects.all()
        for event in events:
            writer.writerow([
                event.title,
                event.status,
                event.start_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                event.end_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                event.current_attendees,
                event.max_attendees or '',
                event.created_by.username
            ])
    
    elif export_type == 'logs':
        response['Content-Disposition'] = 'attachment; filename="system_logs.csv"'
        writer = csv.writer(response)
        writer.writerow(['Level', 'Message', 'Module', 'User', 'Timestamp'])
        
        logs = SystemLogs.objects.all()[:1000]  # Limit to recent 1000 logs
        for log in logs:
            writer.writerow([
                log.level,
                log.message,
                log.module,
                log.user.username if log.user else '',
                log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            ])
    
    return response
