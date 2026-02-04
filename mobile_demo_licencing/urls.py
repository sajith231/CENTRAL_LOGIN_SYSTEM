from django.urls import path
from . import views

app_name = "DemoLicensing"

urlpatterns = [
    path("", views.demo_license_list, name="demo_list"),
    path("add/", views.add_mobile_demo_licencing, name="demo_add"),
    path("edit/<int:pk>/", views.edit_demo_license, name="demo_edit"),
    path("delete/<int:pk>/", views.delete_demo_license, name="demo_delete"),
    path("add-manual/", views.add_manual_demo_license, name="demo_add_manual"),
    path("get-packages/<int:project_id>/", views.get_packages, name="get_packages"),
    path("device/delete/<int:pk>/", views.delete_demo_device, name="demo_device_delete"),

    # AJAX for Dependent Dropdowns
    path("get-branches/", views.get_all_branches, name="get_all_branches"),
    path("get-corporates/<int:branch_id>/", views.get_corporates_by_branch, name="get_corporates_by_branch"),
    path("get-shops/<int:corporate_id>/", views.get_shops_by_corporate, name="get_shops_by_corporate"),
]
