from django.urls import path
from . import views

app_name = 'ModuleAndPackage'

urlpatterns = [
    path('module/', views.module_list, name='module_list'),
    path('module/add/', views.add_module_page, name='add_module_page'),
    path('module/save/', views.add_module, name='add_module'),
    path('module/edit/<int:pk>/', views.edit_module, name='edit_module'),
    path('module/delete/<int:pk>/', views.delete_module, name='delete_module'),
]
