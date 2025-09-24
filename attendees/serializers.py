from rest_framework import serializers
from .models import AttendeeProfile

class AttendeeProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendeeProfile
        # List the fields you want to include in your API
        fields = ['id', 'user', 'job_title', 'interests']