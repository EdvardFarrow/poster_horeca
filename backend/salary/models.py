from django.db import models
from django.conf import settings
from poster_api.models import Category, Product
from shift.models import Shift


class SalaryRule(models.Model):

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="salary_rules"
    )
    # Тип начисления
    FIXED = "fixed"
    PERCENT_SHIFT = "percent_shift"
    PERCENT_CATEGORY = "percent_category"
    PERCENT_PRODUCT = "percent_product"

    RULE_TYPE_CHOICES = [
        (FIXED, "Фиксированная сумма за смену"),
        (PERCENT_SHIFT, "Процент от всей выручки смены"),
        (PERCENT_CATEGORY, "Процент от категории"),
        (PERCENT_PRODUCT, "Процент от позиции"),
    ]

    rule_type = models.CharField(max_length=20, choices=RULE_TYPE_CHOICES)

    # Общие параметры
    value = models.DecimalField(max_digits=10, decimal_places=2,)

    # Для процента от категории
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True,)

    # Для процента от конкретной позиции
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True,)

    def __str__(self):
        return f"{self.employee} - {self.get_rule_type_display()} ({self.value})"


class SalaryRecord(models.Model):
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="salary_records"
    )
    shift = models.ForeignKey(
        Shift,
        on_delete=models.CASCADE,
        related_name="salary_records"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee} | {self.shift} | {self.amount}₽"
