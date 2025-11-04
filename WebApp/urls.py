from django.urls import path
from . import views

app_name = 'WebApp'

urlpatterns = [
    # Web project routes
    path("weblist/", views.web_home, name="webapp_list"),
    path("webproject/create/", views.webproject_create, name="webproject_create"),
    path("webproject/edit/<int:pk>/", views.webproject_edit, name="webproject_edit"),
    path("webproject/delete/<int:pk>/", views.webproject_delete, name="webproject_delete"),

    # Web Control routes
    path("web_control/", views.web_control_list, name="web_control"),
    path("web_control/add/", views.add_web_control, name="add_web_control"),
    path("web_control/edit/<int:pk>/", views.edit_web_control, name="edit_web_control"),
    path("web_control/delete/<int:pk>/", views.delete_web_control, name="delete_web_control"),
    
    # API routes
    # GET: Retrieve all customers data for a project
    path("api/project/<str:endpoint>/", views.api_get_project_data, name="api_get_project"),
    # POST: Log a login attempt
    path("api/project/<str:endpoint>/login/", views.api_post_login, name="api_post_login"),
]