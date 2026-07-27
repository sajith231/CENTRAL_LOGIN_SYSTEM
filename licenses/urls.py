from django.urls import path
from . import views

app_name = 'licenses'

urlpatterns = [
    path('licenses/', views.api_branch_licenses, name='api_branch_licenses'),
]
