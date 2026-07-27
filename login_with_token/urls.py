from django.urls import path
from . import views

app_name = 'login_with_token'

urlpatterns = [
    path('auth/login/', views.api_login, name='api_login'),
    path('auth/logout/', views.api_logout, name='api_logout'),
]
