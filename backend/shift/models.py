from django.db import models
from django.conf import settings



class ShiftParticipation(models.Model):
    shift = models.ForeignKey(
        'Shift',  
        on_delete=models.CASCADE,
        verbose_name="Смена"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Сотрудник"
    )

    role = models.CharField(
        max_length=50,
        verbose_name="Роль в смене (официант, повар, бармен, кальянный мастер, менеджер, санитарный инженер)"
    )
    
    check_in_time = models.DateTimeField(
        verbose_name="Время начала работы"
    )
    check_out_time = models.DateTimeField(
        verbose_name="Время окончания работы",
        null=True, blank=True 
    )

    class Meta:
        unique_together = ('shift', 'user')
        verbose_name = "Участие в смене"
        verbose_name_plural = "Участия в сменах"

    def __str__(self):
        return f"{self.user.username} - {self.role} в смене {self.shift.date}"



class Shift(models.Model):
    # Date & Time
    date = models.DateField(
        verbose_name="Дата смены",
        unique=True
    )
    start_time = models.TimeField(
        verbose_name="Время открытия",
        null=True, blank=True
    )
    end_time = models.TimeField(
        verbose_name= "Время закрытия",
        null=True, blank=True
    )  
    
    # Status
    STATUS_CHOICES = (
        ('OPEN', 'Открыта'),
        ('CLOSED', 'Закрыта'),
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='OPEN',
        verbose_name='Статус смены'
    )      
    
    # Participants
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ShiftParticipation',
        related_name='shifts_worked',
        verbose_name="Участники смены"
    )
    
    # Additional fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Open/Close shift
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='shifts_created',
        verbose_name="Создана менеджером"
    )

    class Meta:
        verbose_name = "Смена"
        verbose_name_plural = "Смены"
        ordering = ['-date', 'start_time']

    def __str__(self):
        return f'Cмена {self.date} ({self.status})'



class PlannedShift(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='planned_shifts',
        verbose_name="Запланированный сотрудник"
    )

    date = models.DateField(
        verbose_name="Дата смены"
    )
    planned_start_time = models.TimeField(
        verbose_name="Плановое время начала"
    )
    planned_end_time = models.TimeField(
        verbose_name="Плановое время окончания"
    )
    
    role = models.CharField(
        max_length=50,
        verbose_name="Роль в смене (официант, повар и т.д.)"
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='schedules_created',
        verbose_name="Внесено менеджером"
    )
    
    class Meta:
        verbose_name = "Запланированная смена"
        verbose_name_plural = "Запланированные смены"
        unique_together = ('user', 'date')
        ordering = ['date', 'planned_start_time']

    def __str__(self):
        return f"План: {self.user.username} - {self.date} ({self.role})"