from django.urls import path
from . import views

app_name = "auto_licence"

urlpatterns = [
    # POST API: Create a Main licence + Corporate + Company in one request
    path("mobileapp/api/project/<str:endpoint>/license/create/", views.api_licence_create, name="api_licence_create"),
]