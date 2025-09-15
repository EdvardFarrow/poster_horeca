from django.db import models

class Employee(models.Model):
    employee_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)




class Category(models.Model):
    category_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    

class CategoriesSales(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='sales')
    profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    count = models.IntegerField(default=0)    

                
class Product(models.Model):
    product_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    category_name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)



class ProductSales(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sales")
    product_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    count = models.IntegerField(default=0)


class Workshop(models.Model):
    workshop_id = models.IntegerField(unique=True)
    workshop_name = models.CharField(max_length=255)
    delete = models.BooleanField(default=False)


class Discount(models.Model):
    discount_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)


class Payments_ID(models.Model):
    payment_method_id = models.IntegerField(unique=True)
    title = models.CharField()
    
    
class Transactions(models.Model):
    transaction_id = models.IntegerField(unique=True)
    date_start = models.DateTimeField()
    date_close = models.DateTimeField()
    status = models.IntegerField()
    pay_type = models.IntegerField()
    payed_sum = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sum = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    spot_id = models.IntegerField()
    transaction_comment = models.CharField(max_length=225, blank=True, null=True)
    reason = models.IntegerField()
    total_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    client_firstname = models.CharField(max_length=225)
    client_lastname = models.CharField(max_length=225)
    client_phone = models.CharField(max_length=20, blank=True, null=True)
    client_id = models.IntegerField(unique=True)
    service_mode = models.IntegerField()
    processing_status = models.IntegerField()
    


class Client(models.Model):
    client_id = models.IntegerField(unique=True)
    firstname = models.CharField(default="")
    lastname = models.CharField(default="")
    name = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transactions = models.IntegerField(default=None)

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
    date_start = models.DateTimeField()  
    date_end = models.DateTimeField(null=True, blank=True)

    cash_start = models.DecimalField(max_digits=10, decimal_places=2, default=0)  
    cash_end = models.DecimalField(max_digits=10, decimal_places=2, default=0)    
    amount_debit = models.DecimalField(max_digits=10, decimal_places=2, default=0)       
    amount_sell_cash = models.DecimalField(max_digits=10, decimal_places=2, default=0) 
    amount_sell_card = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_credit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_collection = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)  
    comment = models.TextField(null=True, blank=True)

    user_id_start = models.IntegerField(null=True, blank=True)
    user_id_end = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Кассовая смена {self.poster_shift_id} ({self.date_start})"



class ShiftSale(models.Model):
    poster_shift_id = models.IntegerField()
    date = models.DateField()
    
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    total_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    total_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    total_delivery_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    total_delivery_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    
    tips = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    
    
    
    
class ShiftSaleItem(models.Model):
    shift_sale = models.ForeignKey(ShiftSale, related_name="items", on_delete=models.CASCADE)
    
    product_name = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_sum = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    department = models.CharField(max_length=255, blank=True, null=True)
    category_name = models.CharField(max_length=255, blank=True, null=True)
    delivery_service = models.CharField(max_length=255, blank=True, null=True)
    