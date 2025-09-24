from events.models import Session

def get_session_recommendations(profile_id: int):
    """
    Dummy function to return the first 3 sessions as recommendations.
    Replace this with your actual AI/ML model logic later.
    """
    # This is a placeholder: it just returns up to 3 random sessions.
    return Session.objects.all().order_by('?')[:3]