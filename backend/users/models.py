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
    
    
class PayGroup(models.Model):
    name = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name="Название группы"
    )
    description = models.TextField(blank=True, null=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Группа расчета ЗП"
        verbose_name_plural = "Группы расчета ЗП"

    def __str__(self):
        return self.name    
    
    
class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    
    pay_group = models.ForeignKey(
        PayGroup, 
        on_delete=models.SET_NULL,  
        null=True, 
        blank=True,                
        related_name="roles",      
        verbose_name="Группа расчета ЗП",
    )

    class Meta:
        verbose_name = "Должность"
        verbose_name_plural = "Должности"

    def __str__(self):
        return self.name

class Employee(models.Model):
    name = models.CharField(max_length=255)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.role})"
    
    
