from django.contrib import admin
from django.urls import path, include
from core import views  # import your core app views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),  # home page
    path("", include("core.urls")),     # include all other core URLs
]
