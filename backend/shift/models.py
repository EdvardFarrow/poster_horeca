from decimal import Decimal
from django.db import models
from django.conf import settings

from poster_api.models import CashShiftReport
from users.models import Employee, Role




class ShiftAssignment(models.Model):
    shift = models.ForeignKey(CashShiftReport, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.employee} на смене {self.shift.poster_shift_id}"    
    
    
class Shift(models.Model):
    poster_shift_id = models.CharField(max_length=100, unique=True)
    date_start = models.DateTimeField()
    date_end = models.DateTimeField(null=True, blank=True)

    employees = models.ManyToManyField(
        Employee,
        through='ShiftEmployee',
        related_name='shifts'
    )



class ShiftEmployee(models.Model):
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)  
    