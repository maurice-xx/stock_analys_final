from django.db import models


# Create your models here.
class SimpleUser(models.Model):
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    user_type = models.IntegerField(default=0)  # 0 for regular user, 1 for admin
