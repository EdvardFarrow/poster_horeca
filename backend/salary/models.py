from django.db import models
from django.conf import settings
from poster_api.models import Product, Workshop
from users.models import Employee, Role
from shift.models import Shift


class SalaryRule(models.Model):
    """
    Defines a single component of a salary calculation for a specific Role.

    This model links a Role to one or more calculation methods:
    1. A fixed amount per shift (`fixed_per_shift`).
    2. A percentage of sales (`percent`) from specific `workshops`.
    3. A fixed bonus per item (`fixed`) for specific `products`.
    """
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    workshops = models.ManyToManyField(Workshop, blank=True)
    products = models.ManyToManyField(Product, through='SalaryRuleProduct', blank=True)
    percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    fixed_per_shift = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Rule for {self.role}"
    
    class Meta:
        verbose_name = "Salary Rule"
        verbose_name_plural = "Salary Rules"

class SalaryRuleProduct(models.Model):
    """
    A 'through' model linking a SalaryRule to a Product.

    This model is crucial as it stores the *specific bonus amount*
    to be paid when this product is sold under this rule.
    """
    salary_rule = models.ForeignKey(SalaryRule, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    fixed = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    
    def __str__(self):
        return f"{self.product.product_name} bonus for {self.salary_rule}"

    class Meta:
        verbose_name = "Salary Product Bonus"
        verbose_name_plural = "Salary Product Bonuses"
        unique_together = ('salary_rule', 'product')



class SalaryRecord(models.Model):
    """
    Stores the final calculated salary for one employee for one shift.

    This acts as a historical record and the source of truth for payroll.
    It breaks down the total salary into its constituent parts
    (fixed, percentage, bonus).
    """
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    total_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fixed_part = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    percent_part = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bonus_part = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    write_off = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    comment = models.CharField(max_length=225, blank=True)

    created_at = models.DateTimeField(auto_now_add=True,)
    updated_at = models.DateTimeField(auto_now=True,)

    class Meta:
        unique_together = ('shift', 'employee')
        verbose_name = "Salary Record"
        verbose_name_plural = "Salary Records"
        
    def __str__(self):
        return f"Salary of {self.employee.name} for shift {self.shift.date}: {self.total_salary}"    
        
        
        
class MonthlySalarySummary(models.Model):
    """
    Aggregated model storing the total salary paid to an employee for one month.    
    """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    month = models.DateField()  # 2025-09-01
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)        
    
    def __str__(self):
        return f"{self.employee.name} - {self.month.strftime('%B %Y')}: {self.total_amount}"

    class Meta:
        verbose_name = "Monthly Salary Summary"
        verbose_name_plural = "Monthly Salary Summaries"
        unique_together = ('employee', 'month')
        ordering = ['-month', 'employee__name']