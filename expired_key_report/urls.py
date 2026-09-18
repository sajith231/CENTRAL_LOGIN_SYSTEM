from django.urls import path

from . import views

app_name = "expired_key_report"

urlpatterns = [
    path("", views.expired_key_report_view, name="expired_key_report"),
]