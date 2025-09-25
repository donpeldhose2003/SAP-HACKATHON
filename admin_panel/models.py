from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class AdminProfile(models.Model):
    ROLE_CHOICES = [
        ('super_admin', 'Super Administrator'),
        ('event_manager', 'Event Manager'),
        ('content_moderator', 'Content Moderator'),
        ('analytics_viewer', 'Analytics Viewer'),
        ('support_agent', 'Support Agent'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='support_agent')
    department = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login_admin = models.DateTimeField(null=True, blank=True)
    is_active_admin = models.BooleanField(default=True)
    permissions = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def update_last_login(self):
        self.last_login_admin = timezone.now()
        self.save()

class SystemSettings(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, default='general')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "System Setting"
        verbose_name_plural = "System Settings"
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}..."

class EventManagement(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True)
    virtual_link = models.URLField(blank=True)
    max_attendees = models.PositiveIntegerField(null=True, blank=True)
    current_attendees = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    tags = models.TextField(help_text="Comma-separated tags", blank=True)
    external_url = models.URLField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Event"
        verbose_name_plural = "Event Management"
    
    def __str__(self):
        return self.title
    
    def get_attendance_percentage(self):
        if self.max_attendees:
            return (self.current_attendees / self.max_attendees) * 100
        return 0

class UserManagement(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_suspended = models.BooleanField(default=False)
    suspension_reason = models.TextField(blank=True)
    suspension_date = models.DateTimeField(null=True, blank=True)
    total_logins = models.PositiveIntegerField(default=0)
    total_chat_messages = models.PositiveIntegerField(default=0)
    total_events_attended = models.PositiveIntegerField(default=0)
    risk_score = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Management"
        verbose_name_plural = "User Management"
    
    def __str__(self):
        return f"Management for {self.user.username}"

class SystemLogs(models.Model):
    LOG_LEVELS = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    level = models.CharField(max_length=10, choices=LOG_LEVELS)
    message = models.TextField()
    module = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "System Log"
        verbose_name_plural = "System Logs"
    
    def __str__(self):
        return f"{self.level}: {self.message[:50]}..."

class Analytics(models.Model):
    metric_name = models.CharField(max_length=100)
    metric_value = models.DecimalField(max_digits=10, decimal_places=2)
    metric_type = models.CharField(max_length=50)  # 'daily', 'weekly', 'monthly'
    date_recorded = models.DateField()
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        unique_together = ['metric_name', 'metric_type', 'date_recorded']
        ordering = ['-date_recorded']
        verbose_name = "Analytics Data"
        verbose_name_plural = "Analytics"
    
    def __str__(self):
        return f"{self.metric_name}: {self.metric_value} ({self.date_recorded})"

class NotificationTemplate(models.Model):
    NOTIFICATION_TYPES = [
        ('welcome', 'Welcome Message'),
        ('event_reminder', 'Event Reminder'),
        ('system_alert', 'System Alert'),
        ('promotional', 'Promotional'),
        ('security', 'Security Alert'),
    ]
    
    name = models.CharField(max_length=100)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    subject = models.CharField(max_length=255)
    template_content = models.TextField()
    variables = models.JSONField(default=list, help_text="List of template variables")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Notification Template"
        verbose_name_plural = "Notification Templates"
    
    def __str__(self):
        return f"{self.name} ({self.get_notification_type_display()})"

class MaintenanceMode(models.Model):
    is_active = models.BooleanField(default=False)
    message = models.TextField(default="System is under maintenance. Please check back later.")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    allowed_users = models.ManyToManyField(User, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='maintenance_created')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Maintenance Mode"
        verbose_name_plural = "Maintenance Mode"
    
    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"Maintenance Mode - {status}"
