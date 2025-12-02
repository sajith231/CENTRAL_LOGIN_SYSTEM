"""
URL configuration for CENTRAL_LOGIN_SYSTEM project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("app1.urls")),   # routes to app1
    path("webapp/", include("WebApp.urls")),   # routes to web_control 
    path("mobileapp/", include("MobileApp.urls")),   
    path('branch/', include('branch.urls')),
    path('store-shop/', include('StoreShop.urls')),
    path('module-package/', include('ModuleAndPackage.urls')),
    path('user-control/', include('user_controll.urls')),
    
]+ (static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) if settings.DEBUG and not settings.CLOUDFLARE_R2_ENABLED else [])
