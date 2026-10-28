from django.urls import path

from . import views


app_name = "financial_year_setup"

urlpatterns = [
    path("", views.financial_year_setup, name="setup"),
    path("create/", views.create_financial_year, name="create"),
    path("<int:financial_year_id>/lock/", views.lock_financial_year, name="lock"),
    path("<int:financial_year_id>/update/", views.update_financial_year, name="update"),
]

