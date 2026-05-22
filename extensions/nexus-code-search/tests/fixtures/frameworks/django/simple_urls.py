"""Fixture: simple Django URL conf with path() and view function references."""
from django.urls import path

from . import views


def home(request):
    return None


def user_detail(request, user_id):
    return None


urlpatterns = [
    path("", home, name="home"),
    path("users/<int:user_id>/", user_detail, name="user-detail"),
    path("about/", views.about, name="about"),
]
