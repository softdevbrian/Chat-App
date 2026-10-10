from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Main Dashboard (PWA Entrypoint)
    path('', views.dashboard_view, name='dashboard'),

    # Authentication & Password Recovery
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/<str:uidb64>/<str:token>/', views.reset_password_confirm_view, name='reset_password_confirm'),

    # REST APIs for Vue Messaging Hub
    path('api/conversations/', views.api_conversations_list, name='api_conversations'),
    path('api/conversations/<int:conversation_id>/messages/', views.api_conversation_messages, name='api_messages'),
    path('api/users/search/', views.api_search_users, name='api_search_users'),
    path('api/dm/start/', views.api_start_dm, name='api_start_dm'),
    path('api/groups/create/', views.api_create_group, name='api_create_group'),
    path('api/groups/<int:group_id>/delete/', views.api_delete_group, name='api_delete_group'),
]
