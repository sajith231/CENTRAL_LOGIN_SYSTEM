from django.urls import path
from . import views

app_name = "user_controll"

urlpatterns = [
    # list all users – for menu control
    path("users/", views.user_menu_user_list, name="user_menu_user_list"),
    # configure menu for one user
    path("users/<int:user_id>/menus/", views.configure_user_menu, name="configure_user_menu"),
]
