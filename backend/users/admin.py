from django.contrib import admin

from .models import (
    PayGroup, 
    Role, 
)

admin.site.register(PayGroup)
admin.site.register(Role)