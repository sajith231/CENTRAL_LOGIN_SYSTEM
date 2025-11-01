from django.urls import path
from . import views

app_name = "MobileApp"

urlpatterns = [
    # List
    path("mobilelist/", views.mobile_home, name="mobileapp_list"),
    # Create
    path("mobileproject/create/", views.mobileproject_create, name="mobileproject_create"),
    # Edit
    path("mobileproject/edit/<int:pk>/", views.mobileproject_edit, name="mobileproject_edit"),
    # Delete
    path("mobileproject/delete/<int:pk>/", views.mobileproject_delete, name="mobileproject_delete"),
]
