from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class AttendeeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    job_title = models.CharField(max_length=200)
    interests = models.TextField(help_text="Comma-separated interests")
    company = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    networking_preferences = models.CharField(
        max_length=20,
        choices=[
            ('open', 'Open to networking'),
            ('selective', 'Selective networking'),
            ('minimal', 'Minimal networking'),
        ],
        default='open'
    )
    first_time_attendee = models.BooleanField(default=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.user.username
    
    def update_last_login(self):
        self.last_login = timezone.now()
        self.save()

class EventInteraction(models.Model):
    INTERACTION_TYPES = [
        ('viewed', 'Viewed'),
        ('registered', 'Registered'),
        ('attended', 'Attended'),
        ('bookmarked', 'Bookmarked'),
        ('rated', 'Rated'),
    ]
    
    attendee = models.ForeignKey(AttendeeProfile, on_delete=models.CASCADE)
    event_id = models.IntegerField()  # Reference to events.Session
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    rating = models.IntegerField(null=True, blank=True, choices=[(i, i) for i in range(1, 6)])
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['attendee', 'event_id', 'interaction_type']
    
    def __str__(self):
        return f"{self.attendee.user.username} {self.interaction_type} event {self.event_id}"