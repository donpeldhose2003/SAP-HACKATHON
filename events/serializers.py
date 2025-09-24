from rest_framework import serializers
from .models import Session, Speaker

class SpeakerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Speaker
        fields = ['id', 'name', 'bio', 'company']

class SessionSerializer(serializers.ModelSerializer):
    speaker = SpeakerSerializer(read_only=True) # Nest speaker info
    class Meta:
        model = Session
        fields = ['id', 'title', 'description', 'start_time', 'speaker']