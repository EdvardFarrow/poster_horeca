from decimal import Decimal
from shift.models import ShiftParticipation
from .models import SalaryRule, SalaryRecord

def calculate_salary_for_shift(shift):
    participations = ShiftParticipation.objects.filter(shift=shift)
    
    for participation in participations:
        employee = participation.user
        rules = SalaryRule.objects.filter(employee=employee)

        total_amount = Decimal(0)

        for rule in rules:
            if rule.rule_type == SalaryRule.FIXED:
                total_amount += rule.value

            elif rule.rule_type == SalaryRule.PERCENT_SHIFT:
                if hasattr(shift, 'revenue'):
                    total_amount += shift.revenue * (rule.value / 100)

            elif rule.rule_type == SalaryRule.PERCENT_CATEGORY:
                category_revenue = shift.get_revenue_by_category(rule.category)
                total_amount += category_revenue * (rule.value / 100)

            elif rule.rule_type == SalaryRule.PERCENT_PRODUCT:
                product_revenue = shift.get_revenue_by_product(rule.product)
                total_amount += product_revenue * (rule.value / 100)

        SalaryRecord.objects.create(
            employee=employee,
            shift=shift,
            amount=total_amount
        )
