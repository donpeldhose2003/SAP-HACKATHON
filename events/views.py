from rest_framework import viewsets
from .models import Session
from .serializers import SessionSerializer

class SessionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Session.objects.all().order_by('start_time')
    serializer_class = SessionSerializer