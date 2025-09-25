from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    # Authentication
    path('login/', views.admin_login, name='login'),
    path('logout/', views.admin_logout, name='logout'),
    
    # Main dashboard
    path('', views.admin_dashboard, name='dashboard'),
    
    # User management
    path('users/', views.user_management, name='user_management'),
    path('users/suspend/<int:user_id>/', views.suspend_user, name='suspend_user'),
    
    # Event management
    path('events/', views.event_management, name='event_management'),
    
    # System settings
    path('settings/', views.system_settings, name='system_settings'),
    
    # Analytics
    path('analytics/', views.analytics_dashboard, name='analytics'),
    
    # System logs
    path('logs/', views.system_logs, name='system_logs'),
    
    # Maintenance mode
    path('maintenance/', views.maintenance_mode, name='maintenance_mode'),
    
    # Data export
    path('export/', views.export_data, name='export_data'),
]