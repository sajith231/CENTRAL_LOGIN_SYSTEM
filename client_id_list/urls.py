from django.urls import path
from .views import get_client_ids

urlpatterns = [
    path('get-client-ids/', get_client_ids, name='get_client_ids'),
]
