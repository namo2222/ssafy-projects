from django.db import models

# Create your models here.
class Book(models.Model):
    RATING_CHOICES = [
        (1, '1점'),
        (2, '2점'),
        (3, '3점'),
        (4, '4점'),
        (5, '5점'),
    ]

    title = models.CharField(max_length=100)
    description = models.TextField()
    rating = models.IntegerField(choices=RATING_CHOICES)
    author = models.CharField(max_length=100)