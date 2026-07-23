"""Django accuracy fixture: URL-conf routes."""
from django.urls import include, path, re_path

from . import views

urlpatterns = [
    path("users/<int:user_id>/", views.user_detail),
    re_path(r"^articles/(?P<year>[0-9]{4})/$", views.year_archive),
    path("admin/", include("admin.urls")),
]
