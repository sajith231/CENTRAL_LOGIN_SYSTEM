from django.urls import path

from . import views

app_name = "trellisco_hub_report"

urlpatterns = [
    path("", views.trellisco_hub_report_view, name="trellisco_hub_report"),
]