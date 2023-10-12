from django.db import models


__all__ = ("Author", "Book")


class Author(models.Model):
    name = models.CharField(max_length=32)
    age = models.PositiveIntegerField(default=0)


class Book(models.Model):
    author = models.ForeignKey(Author, models.CASCADE)
    title = models.CharField(max_length=32)
    year = models.PositiveIntegerField(default=0)
