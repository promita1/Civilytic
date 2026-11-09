from django.contrib import admin
from django.urls import include, path

from benefits import views

urlpatterns = [
    path("", views.index),
    path("admin/", admin.site.urls),
    path("api/", include("benefits.urls")),
]