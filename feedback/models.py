# Create your models here.
from django.db import models
from django.utils import timezone


class Feedback(models.Model):
    username = models.CharField(max_length=100)
    submit_time = models.DateTimeField(default=timezone.now)
    content = models.TextField()
    contact = models.CharField(max_length=100)

    def __str__(self):
        return self.username
