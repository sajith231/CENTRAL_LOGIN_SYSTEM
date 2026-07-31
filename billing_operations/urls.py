from django.urls import path
from . import views

app_name = 'billing_operations'

urlpatterns = [
    path('unbilled/', views.api_unbilled_licenses, name='api_unbilled_licenses'),
    path('bill/', views.api_bill_license, name='api_bill_license'),
]
