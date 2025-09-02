from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('owner', 'Управляющий'),
        ('manager', 'Менеджер'),
        ('employee', 'Сотрудник'),
        ('waiter', 'Официант'),
        ('bartender', 'Бармен'),
        ('cook', 'Повар'),
        ('hookah', 'Кальянщик'),
        ('cleaner', 'Уборщик'),
        ('trainee', 'Стажер'), 
        ('delivery', 'Доставка'), 

    )
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='trainee')
    fullname = models.CharField(max_length=150, blank=True)
    

    
    def __str__(self):
        return self.username    