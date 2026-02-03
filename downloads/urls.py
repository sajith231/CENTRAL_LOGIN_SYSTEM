from django.urls import path
from . import views

app_name = "downloads"

urlpatterns = [
    path("upload/", views.upload_page, name="upload"),
    path("delete/<str:name>/", views.delete_folder, name="delete_folder"),
    path("download/", views.download_page, name="download"),
    path("download/<str:folder>/<str:filename>/", views.download_file, name="download_file"),
]