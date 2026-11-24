from django.urls import path

from . import views

app_name = "new_licence_report"

urlpatterns = [
    path("", views.new_licence_report_view, name="new_licence_report"),
    path("terp/", views.terp_new_licence_report_view, name="terp_new_licence_report"),
]
