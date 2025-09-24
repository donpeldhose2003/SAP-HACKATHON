from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('create-profile/', views.create_profile, name='create_profile'),
    path('api/log-activity/', views.log_activity, name='log_activity'),
    path('api/feed/', views.get_feed_api, name='get_feed_api'),
    path('api/event-interaction/', views.event_interaction, name='event_interaction'),
    path('about/', views.about, name='about'),
    path('features/', views.features, name='features'),
    path('test-websocket/', views.test_websocket, name='test_websocket'),
]