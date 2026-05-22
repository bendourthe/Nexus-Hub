"""Fixture: Django URL conf with re_path() and a class-based view."""
from django.urls import re_path
from django.views.generic import TemplateView


class YearArchiveView(TemplateView):
    template_name = "year.html"


def article_detail(request, slug):
    return None


urlpatterns = [
    re_path(r"^articles/(?P<year>[0-9]{4})/$", YearArchiveView.as_view()),
    re_path(r"^articles/(?P<slug>[-\w]+)/$", article_detail),
]
