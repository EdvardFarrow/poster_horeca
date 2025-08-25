from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('owner', 'Владелец'),
        ('manager', 'Менеджер'),
        ('employee', 'Сотрудник')
    )
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='manager')
    fullname = models.CharField(max_length=150, blank=True)

    
    def __str__(self):
        return self.username    