from django.contrib import admin

from .models import (
    SalaryRule, 
    SalaryRuleProduct, 
)

admin.site.register(SalaryRule)
admin.site.register(SalaryRuleProduct)