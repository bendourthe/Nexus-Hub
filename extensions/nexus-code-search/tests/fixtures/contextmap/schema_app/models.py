"""Schema accuracy fixture: Django models with relations + a decoy class."""
from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=100, unique=True)
    email = models.EmailField()


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    tags = models.ManyToManyField("Tag")

    class Meta:
        ordering = ["title"]


class PlainService:
    """Not an ORM model - must not be detected."""

    def run(self):
        return 1
