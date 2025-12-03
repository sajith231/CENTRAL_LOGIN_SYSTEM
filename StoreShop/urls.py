from django.urls import path
from . import views

urlpatterns = [
    # Store URLs
    path('stores/', views.stores_list, name='stores_list'),
    path('stores/add/', views.add_store, name='add_store'),
    path('stores/edit/<int:id>/', views.edit_store, name='edit_store'),
    path('stores/delete/<int:id>/', views.delete_store, name='delete_store'),

    # Shop URLs
    path('shops/', views.shop_list, name='shop_list'),
    path('shops/add/', views.add_shop, name='add_shop'),
    path('shops/edit/<int:id>/', views.edit_shop, name='edit_shop'),
    path('shops/delete/<int:id>/', views.delete_shop, name='delete_shop'),
]
