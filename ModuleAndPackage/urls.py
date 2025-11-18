from django.urls import path
from . import views

app_name = 'ModuleAndPackage'

urlpatterns = [
    path('module/', views.module_list, name='module_list'),
    path('module/add/', views.add_module_page, name='add_module_page'),
    path('module/save/', views.add_module, name='add_module'),
    path('module/edit/<int:pk>/', views.edit_module, name='edit_module'),
    path('module/delete/<int:pk>/', views.delete_module, name='delete_module'),

    path('packages/', views.package_list, name='package_list'),
    path('packages/add/', views.add_package_page, name='add_package_page'),
    path('packages/save/', views.save_package, name='save_package'),
    path('packages/edit/<int:pk>/', views.edit_package, name='edit_package'),
    path('packages/delete/<int:pk>/', views.delete_package, name='delete_package'),
    path("get-modules/<int:project_id>/", views.get_modules, name="get_modules"),
]
