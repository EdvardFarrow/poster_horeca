from django.db import models
from django.conf import settings
from poster_api.models import CashShiftReport, Product
from users.models import Employee, Role
from poster_api.models import Workshop



class SalaryRule(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    workshops = models.ManyToManyField(Workshop, blank=True)
    products = models.ManyToManyField(Product, through='SalaryRuleProduct', blank=True)
    percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    fixed_per_shift = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Правило для {self.role}"

class SalaryRuleProduct(models.Model):
    salary_rule = models.ForeignKey(SalaryRule, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    fixed = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)



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