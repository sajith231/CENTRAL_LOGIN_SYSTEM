from django.urls import path

from . import views

app_name = 'agents'

urlpatterns = [
    path('', views.agent_list, name='agent_list'),
    path('add/', views.agent_add, name='agent_add'),
    path('edit/<int:pk>/', views.agent_edit, name='agent_edit'),
    path('delete/<int:pk>/', views.agent_delete, name='agent_delete'),
    # Public API: register a customer mail id against an agent referral code
    path('api/agent-referral/', views.api_agent_referral, name='api_agent_referral'),
]
