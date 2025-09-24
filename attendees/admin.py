from django.contrib import admin
from .models import AttendeeProfile, EventInteraction

@admin.register(AttendeeProfile)
class AttendeeProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'job_title', 'company', 'networking_preferences', 'first_time_attendee', 'registration_date']
    list_filter = ['networking_preferences', 'first_time_attendee', 'registration_date']
    search_fields = ['user__username', 'user__email', 'job_title', 'company']
    readonly_fields = ['registration_date', 'last_login']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'job_title', 'company')
        }),
        ('Preferences', {
            'fields': ('interests', 'bio', 'networking_preferences', 'first_time_attendee')
        }),
        ('Timestamps', {
            'fields': ('registration_date', 'last_login'),
            'classes': ('collapse',)
        }),
    )

@admin.register(EventInteraction)
class EventInteractionAdmin(admin.ModelAdmin):
    list_display = ['attendee', 'event_id', 'interaction_type', 'rating', 'timestamp']
    list_filter = ['interaction_type', 'rating', 'timestamp']
    search_fields = ['attendee__user__username', 'event_id']
    readonly_fields = ['timestamp']