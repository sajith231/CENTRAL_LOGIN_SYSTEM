from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    path('customers/', views.api_customers, name='api_customers'),
]
