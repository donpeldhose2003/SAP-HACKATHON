from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta
from .models import ChatSession, ChatMessage, UserActivity, UserPreferences

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_id', 'created_at', 'last_activity', 'is_active', 'message_count', 'session_duration']
    list_filter = ['is_active', 'created_at', 'last_activity']
    search_fields = ['user__username', 'user__email', 'session_id']
    readonly_fields = ['created_at', 'last_activity', 'session_duration', 'message_count']
    date_hierarchy = 'created_at'
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'
    
    def session_duration(self, obj):
        if obj.last_activity and obj.created_at:
            duration = obj.last_activity - obj.created_at
            hours = duration.total_seconds() / 3600
            return f"{hours:.1f} hours"
        return "N/A"
    session_duration.short_description = 'Duration'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').annotate(
            msg_count=Count('messages')
        )

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session_user', 'message_type', 'content_preview', 'timestamp', 'message_length']
    list_filter = ['message_type', 'timestamp']
    search_fields = ['content', 'session__user__username', 'session__user__email']
    readonly_fields = ['timestamp', 'message_length']
    date_hierarchy = 'timestamp'
    
    def session_user(self, obj):
        return obj.session.user.username
    session_user.short_description = 'User'
    session_user.admin_order_field = 'session__user__username'
    
    def content_preview(self, obj):
        preview = obj.content[:80] + "..." if len(obj.content) > 80 else obj.content
        if obj.message_type == 'user':
            return format_html('<span style="color: #0066cc;">{}</span>', preview)
        elif obj.message_type == 'bot':
            return format_html('<span style="color: #009900;">{}</span>', preview)
        elif obj.message_type == 'welcome':
            return format_html('<span style="color: #ff6600;">{}</span>', preview)
        return preview
    content_preview.short_description = 'Content'
    
    def message_length(self, obj):
        return len(obj.content)
    message_length.short_description = 'Length'

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_type', 'timestamp']
    list_filter = ['activity_type', 'timestamp']
    search_fields = ['user__username', 'activity_type']
    readonly_fields = ['timestamp']

@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_frequency', 'timezone', 'language']
    list_filter = ['notification_frequency', 'language']
    search_fields = ['user__username']
