from django.db import models

class Employee(models.Model):
    employee_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)


class Client(models.Model):
    client_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)


class Product(models.Model):
    product_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    category_id = models.IntegerField()
    category_name = models.CharField(max_length=255)


class Category(models.Model):
    category_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)


class Department(models.Model):
    department_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)


class Discount(models.Model):
    discount_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)


class AnalyticsRecord(models.Model):
    
    TYPE_CHOICES = [
        ("finance", "Finance"),
        ("sales", "Sales"),
        ("products", "Products"),
        ("categories", "Categories"),
        ("clients", "Clients"),
        ("employees", "Employees"),
        ("discounts", "Discounts"),
        ("departments", "Departments"),
    ]

    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    entity_id = models.IntegerField(null=True, blank=True)
    date = models.DateField()
    data = models.JSONField()  




class CashShiftReport(models.Model):
    poster_shift_id = models.CharField(max_length=100, unique=True)  
    cash_start = models.DecimalField(max_digits=10, decimal_places=2, default=0)  
    cash_end = models.DecimalField(max_digits=10, decimal_places=2, default=0)    
    sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)       
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0) 
    date_start = models.DateTimeField()  
    date_end = models.DateTimeField(null=True, blank=True)  

    def __str__(self):
        return f"Кассовая смена {self.poster_shift_id} ({self.organization_id})"
