from django.db import models
from users.models import Employee, Role



class Shift(models.Model):
    """
    Represents a single work shift on a specific date.
    """
    shift_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    date = models.DateField(default='2025-10-01')
    employees = models.ManyToManyField(
        Employee,
        through='ShiftEmployee',
        related_name='shifts'
    )
    
    def __str__(self):
        return f"Shift on {self.date} (ID: {self.shift_id or self.id})"

    class Meta:
        verbose_name = _("Work Shift")
        verbose_name_plural = _("Work Shifts")
        ordering = ['-date']


class ShiftEmployee(models.Model):
    """
    A 'through' model connecting an Employee to a Shift, and assigning
    their Role for that specific shift.
    """
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)  
    
    def __str__(self):
        return f"{self.employee.name} as {self.role.name} on {self.shift.date}"

    class Meta:
        verbose_name = _("Shift-Employee Assignment")
        verbose_name_plural = _("Shift-Employee Assignments")
        unique_together = ('shift', 'employee', 'role')