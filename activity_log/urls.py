from django.urls import path

from . import views

app_name = "activity_log"

urlpatterns = [
    path("", views.activity_log_view, name="activity_log"),
    path("delete-month/", views.activity_log_delete_month, name="activity_log_delete_month"),
]
