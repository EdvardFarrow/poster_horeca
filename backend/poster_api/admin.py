from django.contrib import admin
from .models import (
    Workshop, 
    Product
)

admin.site.register(Workshop)
admin.site.register(Product)