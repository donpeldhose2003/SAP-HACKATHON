from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import connection
from django.core.cache import cache
from chat.models import ChatSession, UserActivity
from attendees.models import AttendeeProfile
import time
import json

@require_http_methods(["GET"])
def health_check(request):
    """
    Health check endpoint for monitoring system status
    """
    start_time = time.time()
    
    try:
        # Database connectivity test
        db_status = "ok"
        db_response_time = None
        try:
            db_start = time.time()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            db_response_time = round((time.time() - db_start) * 1000, 2)
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        # Cache connectivity test
        cache_status = "ok"
        cache_response_time = None
        try:
            cache_start = time.time()
            cache.set('health_check', 'ok', 10)
            cache.get('health_check')
            cache_response_time = round((time.time() - cache_start) * 1000, 2)
        except Exception as e:
            cache_status = f"error: {str(e)}"
        
        # Basic metrics
        active_sessions = ChatSession.objects.filter(is_active=True).count()
        total_users = AttendeeProfile.objects.count()
        
        # Response time
        total_response_time = round((time.time() - start_time) * 1000, 2)
        
        # Overall status
        overall_status = "healthy" if db_status == "ok" and cache_status == "ok" else "degraded"
        
        return JsonResponse({
            "status": overall_status,
            "timestamp": timezone.now().isoformat(),
            "services": {
                "database": {
                    "status": db_status,
                    "response_time_ms": db_response_time
                },
                "cache": {
                    "status": cache_status,
                    "response_time_ms": cache_response_time
                }
            },
            "metrics": {
                "active_sessions": active_sessions,
                "total_users": total_users,
                "total_response_time_ms": total_response_time
            }
        })
        
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "error": str(e),
            "timestamp": timezone.now().isoformat()
        }, status=500)

@require_http_methods(["GET"])
def system_metrics(request):
    """
    Detailed system metrics for monitoring
    """
    try:
        from datetime import timedelta
        now = timezone.now()
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)
        
        # Session metrics
        sessions_last_hour = ChatSession.objects.filter(
            created_at__gte=last_hour
        ).count()
        
        sessions_last_day = ChatSession.objects.filter(
            created_at__gte=last_day
        ).count()
        
        # Activity metrics
        activities_last_hour = UserActivity.objects.filter(
            timestamp__gte=last_hour
        ).count()
        
        # User metrics
        active_users_today = ChatSession.objects.filter(
            last_activity__gte=last_day
        ).values('user').distinct().count()
        
        return JsonResponse({
            "timestamp": now.isoformat(),
            "sessions": {
                "last_hour": sessions_last_hour,
                "last_24h": sessions_last_day
            },
            "activities": {
                "last_hour": activities_last_hour
            },
            "users": {
                "active_today": active_users_today
            }
        })
        
    except Exception as e:
        return JsonResponse({
            "error": str(e),
            "timestamp": timezone.now().isoformat()
        }, status=500)