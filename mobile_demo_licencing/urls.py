from django.urls import path
from . import views

app_name = "DemoLicensing"

urlpatterns = [
    path("", views.demo_license_list, name="demo_list"),
    path("add/", views.add_mobile_demo_licencing, name="demo_add"),
    path("edit/<int:pk>/", views.edit_demo_license, name="demo_edit"),
    path("delete/<int:pk>/", views.delete_demo_license, name="demo_delete"),
    path("add-manual/", views.add_manual_demo_license, name="demo_add_manual"),
    path("get-packages/<int:project_id>/", views.get_packages, name="get_packages")
]
