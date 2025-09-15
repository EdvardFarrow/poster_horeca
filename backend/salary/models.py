from django.db import models
from django.conf import settings
from poster_api.models import CashShiftReport
from users.models import Employee, Role



class SalaryRule(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE,default=None)
    category_name = models.CharField(max_length=255, blank=True, null=True)  
    percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # % от выручки
    fixed_per_shift = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # фикс за смену
    fixed_per_item = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # фикс за товар (например, кальян)
    product_name = models.CharField(max_length=255, blank=True, null=True)  # например, "Кальян на грейпфруте"

    def __str__(self):
        return f"Правило для {self.role}"



class SalaryRecord(models.Model):
    shift = models.ForeignKey(CashShiftReport, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        unique_together = ('shift', 'employee')
        
        
        
class MonthlySalarySummary(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    month = models.DateField()  # 2025-09-01
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)        