from django.db import models

from fox.etl.models import Model


__all__ = ("Author", "Book")


class Author(Model):
    name = models.CharField(max_length=32)
    age = models.PositiveIntegerField(default=0)


class Book(Model):
    author = models.ForeignKey(Author, models.CASCADE)
    title = models.CharField(max_length=32)
    year = models.PositiveIntegerField(default=0)
