from django.urls import path
from . import views

app_name = "auto_licence"

urlpatterns = [
    # POST API: Create a DEMO licence + Corporate + Company in one request
    path("mobileapp/api/project/<str:endpoint>/license/create/", views.api_licence_create, name="api_licence_create"),
    # POST API: Super User converts a DEMO licence to a Main licence
    path("mobileapp/api/licence/<int:pk>/convert/", views.convert_demo_to_main, name="convert_demo_to_main"),
]