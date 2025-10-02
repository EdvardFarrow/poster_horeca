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
    category_id = models.IntegerField(unique=True, default=1)
    category_name = models.CharField(max_length=225, default="")
    profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    count = models.IntegerField(default=0)    

                
class Product(models.Model):
    product_id = models.IntegerField(unique=True)
    product_name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.SET_DEFAULT, default=1)    
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fiscal = models.IntegerField(default=1)
    workshop = models.IntegerField(default=0)
    



class ProductSales(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sales")
    product_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    count = models.IntegerField(default=0)


class Workshop(models.Model):
    workshop_id = models.IntegerField(unique=True)
    workshop_name = models.CharField(max_length=255)
    delete = models.BooleanField(default=False)


class Payments_ID(models.Model):
    payment_method_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=225)
    

class Clients(models.Model):
    client_id = models.IntegerField(default=1)
    firstname = models.CharField(default="")
    lastname = models.CharField(default="")
    name = models.CharField(max_length=255,  blank=True, default="")
    phone = models.CharField(max_length=50,  blank=True, default="")
    email = models.EmailField(null=True, blank=True)
    revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transactions = models.IntegerField(default=0)
    avg_check = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    
class Transactions(models.Model):
    transaction_id = models.IntegerField(null=True, blank=True)
    date_start = models.DateTimeField()
    date_close = models.DateTimeField()
    status = models.IntegerField(default=0)
    pay_type = models.IntegerField(default=0)
    payed_sum = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sum = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    spot_id = models.IntegerField(default=1)
    transaction_comment = models.CharField(max_length=225, blank=True, null=True)
    reason = models.CharField(default="")
    total_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    client_firstname = models.CharField(max_length=225, blank=True)
    client_lastname = models.CharField(max_length=225, blank=True)
    client_phone = models.CharField(max_length=20, blank=True, null=True)
    client_id = models.CharField(default="", null=True, blank=True)
    service_mode = models.IntegerField(default=0)
    processing_status = models.IntegerField(default=0)
    
    
class TransactionsProducts(models.Model):
    transaction = models.ForeignKey(Transactions, on_delete=models.CASCADE, related_name="products")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="transaction_entries")
    num = models.IntegerField(default=0)
    workshop = models.IntegerField(default=0)
    payed_sum = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    client = models.ForeignKey(Clients, on_delete=models.CASCADE, related_name="transaction_entries", null=True, blank=True)
    product_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    product_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    
class TransactionHistory(models.Model):
    transaction = models.ForeignKey(Transactions, on_delete=models.CASCADE, related_name="history")
    type_history = models.CharField(max_length=50)
    time = models.DateTimeField()
    value = models.CharField(default="")
    value2 = models.CharField(default="")
    value3 = models.CharField(default="")
    value_text = models.JSONField(null=True, blank=True)
    spot_tablet_id = models.IntegerField(null=True, blank=True)



class AnalyticsRecord(models.Model):
    
    TYPE_CHOICES = [
        ("sales", "Sales"),
        ("products", "Products"),
        ("categories", "Categories"),
        ("clients", "Clients"),
        ("employees", "Employees"),
        ("workshop", "Workshop"),
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
    shift_id = models.IntegerField()
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
    count = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    product_sum = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payed_sum = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    workshop = models.CharField(max_length=255, blank=True, null=True)
    category_name = models.CharField(max_length=255, blank=True, null=True)
    delivery_service = models.CharField(max_length=255, blank=True, null=True)
    tips = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    