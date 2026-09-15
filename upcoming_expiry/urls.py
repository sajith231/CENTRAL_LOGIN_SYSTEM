from django.urls import path

from . import views

app_name = "upcoming_expiry"

urlpatterns = [
    path("", views.upcoming_expiry_view, name="upcoming_expiry"),
]