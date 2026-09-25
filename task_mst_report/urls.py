from django.urls import path

from . import views

app_name = "task_mst_report"

urlpatterns = [
    path("", views.task_mst_report_view, name="task_mst_report"),
]