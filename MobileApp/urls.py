from django.urls import path
from . import views

app_name = 'MobileApp'

urlpatterns = [
    # Mobile project routes
    path("mobilelist/", views.mobile_home, name="mobileapp_list"),
    path("mobileproject/create/", views.mobileproject_create, name="mobileproject_create"),
    path("mobileproject/edit/<int:pk>/", views.mobileproject_edit, name="mobileproject_edit"),
    path("mobileproject/delete/<int:pk>/", views.mobileproject_delete, name="mobileproject_delete"),

    # Mobile Control routes
    path("mobile_control/", views.mobile_control_list, name="mobile_control"),
    path("mobile_control/add/", views.add_mobile_control, name="add_mobile_control"),
    path("mobile_control/edit/<int:pk>/", views.edit_mobile_control, name="edit_mobile_control"),
    path("mobile_control/delete/<int:pk>/", views.delete_mobile_control, name="delete_mobile_control"),
    
    # API routes
    # GET: Retrieve all customers data for a project
    path("api/project/<str:endpoint>/", views.api_get_project_data, name="api_get_project"),
    path("api/project/<str:endpoint>/license/register/", views.api_register_license, name="api_register_license"),
    # POST: Log a login attempt
    path("api/project/<str:endpoint>/login/", views.api_post_login, name="api_post_login"),
    path("api/project/<str:endpoint>/logout/", views.api_post_logout, name="api_post_logout"),
]
