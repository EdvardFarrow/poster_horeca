from django.db import models
from users.models import Employee, Role



class Shift(models.Model):
    shift_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    date = models.DateField(default='2025-10-01')
    

    employees = models.ManyToManyField(
        Employee,
        through='ShiftEmployee',
        related_name='shifts'
    )


class ShiftEmployee(models.Model):
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)  
    