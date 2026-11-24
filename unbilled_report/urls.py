from django.urls import path

from . import views

app_name = "unbilled_report"

urlpatterns = [
    path("", views.unbilled_report, name="unbilled_report"),
    path("terp/", views.terp_unbilled_report, name="terp_unbilled_report"),
]