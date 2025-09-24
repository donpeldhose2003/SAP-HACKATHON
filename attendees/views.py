from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from .models import AttendeeProfile
from .serializers import AttendeeProfileSerializer
from events.serializers import SessionSerializer
from ai_engine import recommendation


# View 1: A standalone function to render your HTML page
def home_view(request):
    return render(request, 'index.html')


# View 2: A ViewSet for handling Attendee Profile data
class AttendeeProfileViewSet(viewsets.ModelViewSet):
    queryset = AttendeeProfile.objects.all()
    serializer_class = AttendeeProfileSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'])
    def recommendations(self, request, pk=None):
        profile = self.get_object()
        recommended_sessions = recommendation.get_session_recommendations(profile.id)
        serializer = SessionSerializer(recommended_sessions, many=True)
        return Response(serializer.data)


# View 3: A dedicated API view for the dynamic timeline feed
class TimelineAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        
        try:
            profile = user.attendeeprofile
        except AttendeeProfile.DoesNotExist:
            return Response({"error": "Attendee profile not found."}, status=404)

        # Get personalized session recommendations
        recommendations = recommendation.get_session_recommendations(profile.id)
        
        timeline_items = [
            {'type': 'recommendation', 'title': rec.title, 'time': rec.start_time} for rec in recommendations
        ]
        
        sorted_items = sorted(timeline_items, key=lambda x: x['time'])

        return Response(sorted_items)