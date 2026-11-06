from django.urls import path
from . import views

app_name = "auto_licence"

urlpatterns = [
    # T-ERP POST API: Create licences for one or more projects in one request
    path(
        "t-erp/mobileapp/api/license/create/",
        views.api_licence_create,
        {"t_erp_only": True},
        name="t_erp_api_licence_create",
    ),

    # Compatibility alias for clients that append the mobile API path twice.
    path(
        "t-erp/mobileapp/api/license/create/mobileapp/api/license/create/",
        views.api_licence_create,
        {"t_erp_only": True},
        name="t_erp_api_licence_create_duplicated",
    ),

]
