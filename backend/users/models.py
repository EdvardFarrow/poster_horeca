from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('owner', 'Владелец'),
        ('manager', 'Менеджер'),
    )
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='manager')
    
    def __str__(self):
        return self.username