from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    AdminProfile, SystemSettings, EventManagement, UserManagement,
    SystemLogs, Analytics, NotificationTemplate, MaintenanceMode
)

class AdminProfileInline(admin.StackedInline):
    model = AdminProfile
    can_delete = False
    verbose_name_plural = 'Admin Profile'
    fk_name = 'user'

class CustomUserAdmin(BaseUserAdmin):
    inlines = (AdminProfileInline,)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'department', 'is_active_admin', 'created_at', 'last_login_admin')
    list_filter = ('role', 'is_active_admin', 'department', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'last_login_admin')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'role', 'department', 'phone_number')
        }),
        ('Status', {
            'fields': ('is_active_admin', 'created_at', 'last_login_admin')
        }),
        ('Permissions', {
            'fields': ('permissions',),
            'classes': ('collapse',)
        }),
    )

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('key', 'category', 'is_active', 'created_by', 'updated_at')
    list_filter = ('category', 'is_active', 'updated_at')
    search_fields = ('key', 'value', 'description')
    readonly_fields = ('updated_at',)
    
    fieldsets = (
        (None, {
            'fields': ('key', 'value', 'description', 'category')
        }),
        ('Status', {
            'fields': ('is_active', 'created_by', 'updated_at')
        }),
    )

@admin.register(EventManagement)
class EventManagementAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'priority', 'start_datetime', 'current_attendees', 'max_attendees', 'created_by')
    list_filter = ('status', 'priority', 'created_at', 'start_datetime')
    search_fields = ('title', 'description', 'tags', 'location')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'status', 'priority', 'tags')
        }),
        ('Event Details', {
            'fields': ('start_datetime', 'end_datetime', 'location', 'virtual_link', 'external_url')
        }),
        ('Attendance', {
            'fields': ('max_attendees', 'current_attendees')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_attendance_percentage(self, obj):
        return f"{obj.get_attendance_percentage():.1f}%"
    get_attendance_percentage.short_description = "Attendance %"

@admin.register(UserManagement)
class UserManagementAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_suspended', 'total_logins', 'total_chat_messages', 'risk_score', 'updated_at')
    list_filter = ('is_suspended', 'risk_score', 'created_at')
    search_fields = ('user__username', 'user__email', 'notes')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('user',)
        }),
        ('Status', {
            'fields': ('is_suspended', 'suspension_reason', 'suspension_date')
        }),
        ('Statistics', {
            'fields': ('total_logins', 'total_chat_messages', 'total_events_attended', 'risk_score')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(SystemLogs)
class SystemLogsAdmin(admin.ModelAdmin):
    list_display = ('level', 'message_short', 'module', 'user', 'timestamp')
    list_filter = ('level', 'module', 'timestamp')
    search_fields = ('message', 'module', 'user__username')
    readonly_fields = ('timestamp',)
    
    def message_short(self, obj):
        return obj.message[:100] + "..." if len(obj.message) > 100 else obj.message
    message_short.short_description = "Message"

@admin.register(Analytics)
class AnalyticsAdmin(admin.ModelAdmin):
    list_display = ('metric_name', 'metric_value', 'metric_type', 'date_recorded')
    list_filter = ('metric_type', 'date_recorded', 'metric_name')
    search_fields = ('metric_name',)
    
    fieldsets = (
        (None, {
            'fields': ('metric_name', 'metric_value', 'metric_type', 'date_recorded')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'notification_type', 'is_active', 'created_by', 'updated_at')
    list_filter = ('notification_type', 'is_active', 'created_at')
    search_fields = ('name', 'subject', 'template_content')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'notification_type', 'subject')
        }),
        ('Template', {
            'fields': ('template_content', 'variables')
        }),
        ('Status', {
            'fields': ('is_active', 'created_by', 'created_at', 'updated_at')
        }),
    )

@admin.register(MaintenanceMode)
class MaintenanceModeAdmin(admin.ModelAdmin):
    list_display = ('is_active', 'start_time', 'end_time', 'created_by', 'created_at')
    list_filter = ('is_active', 'created_at')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('is_active', 'message')
        }),
        ('Schedule', {
            'fields': ('start_time', 'end_time')
        }),
        ('Access', {
            'fields': ('allowed_users',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at')
        }),
    )

# Customize admin site
admin.site.site_header = "AURA Admin Panel"
admin.site.site_title = "AURA Admin"
admin.site.index_title = "Welcome to AURA Administration"
