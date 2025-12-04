from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("login/", views.login_view, name="login"),
    path("dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("logout/", views.logout_view, name="logout"),
    path("users/", views.users_table, name="users_table"),
    path("users/add/", views.add_user, name="add_user"),
    path("users/<int:pk>/edit/", views.edit_user, name="edit_user"),
    path("users/<int:pk>/delete/", views.delete_user, name="delete_user"),
]