from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.branch_list, name='branch_list'),
    path('add/', views.add_branch, name='add_branch'),
    path('edit/<int:id>/', views.edit_branch, name='edit_branch'),
    path('delete/<int:id>/', views.delete_branch, name='delete_branch'),
]