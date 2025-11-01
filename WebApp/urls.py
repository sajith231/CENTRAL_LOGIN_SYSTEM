from django.urls import path
from . import views

# App name for namespacing (optional but recommended)
app_name = 'WebApp'

urlpatterns = [
    # List view - Display all web projects in a table
    # URL: /webapp/weblist/
    path("weblist/", views.web_home, name="webapp_list"),
    
    # Create view - Form to add new web project
    # URL: /webapp/webproject/create/
    path("webproject/create/", views.webproject_create, name="webproject_create"),
    
    # Edit view - Form to update existing web project
    # URL: /webapp/webproject/edit/1/ (where 1 is the project ID)
    path("webproject/edit/<int:pk>/", views.webproject_edit, name="webproject_edit"),
    
    # Delete view - Remove a web project (called from modal)
    # URL: /webapp/webproject/delete/1/ (where 1 is the project ID)
    path("webproject/delete/<int:pk>/", views.webproject_delete, name="webproject_delete"),
]