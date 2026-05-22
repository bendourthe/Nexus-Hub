"""Fixture: Django URL conf with nested include()."""
from django.urls import include, path


def health(request):
    return None


urlpatterns = [
    path("health/", health),
    path("api/v1/", include("myproject.api.urls")),
    path("admin/", include("django.contrib.admin.urls")),
]
