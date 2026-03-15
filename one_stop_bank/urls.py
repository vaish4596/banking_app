from django.contrib import admin
from django.urls import path, include
from core import views as core_views

urlpatterns = [
    path("", core_views.home, name="home"),
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
]
