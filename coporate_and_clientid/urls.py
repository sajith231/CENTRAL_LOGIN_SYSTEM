from django.urls import path
from .views import corporate_and_clientid_list

urlpatterns = [
    path('list/', corporate_and_clientid_list, name='corporate_clientid_list'),
]
