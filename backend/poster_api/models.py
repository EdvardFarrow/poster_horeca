from django.db import models

class Employee(models.Model):
    """Represents an employee or user of the POS system."""
    employee_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
        
    class Meta:
        verbose_name = "Employee"
        verbose_name_plural = "Employees"

class Category(models.Model):
    """Represents a product category."""
    category_id = models.IntegerField(unique=True)
    category_name = models.CharField(max_length=255, null=True)
    
    def __str__(self):
        return self.category_name or f"Category {self.category_id}"

    class Meta:
        verbose_name = "Product Category"
        verbose_name_plural = "Product Categories"


class CategoriesSales(models.Model):
    """
    Stores aggregated sales data (profit, count) grouped by Category.
    """
    category = models.ForeignKey(Category, on_delete=models.SET_DEFAULT, default=1)    
    profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    count = models.IntegerField(default=0)    

    class Meta:
        verbose_name = "Category Sale Aggregate"
        verbose_name_plural = "Category Sale Aggregates"

class Product(models.Model):
    """Represents an individual product or menu item that can be sold."""
    product_id = models.IntegerField(unique=True)
    product_name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.SET_DEFAULT, default=1)    
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fiscal = models.IntegerField(default=1)
    workshop = models.IntegerField(default=0)
    
    def __str__(self):
        return self.product_name


class ProductSales(models.Model):
    """
    Stores aggregated sales data (profit, count) grouped by Product.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sales")
    product_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    count = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Product Sale Aggregate"
        verbose_name_plural = "Product Sale Aggregates"


class Workshop(models.Model):
    """Represents a preparation area or 'workshop' (e.g., 'Kitchen', 'Bar')."""
    workshop_id = models.IntegerField(unique=True)
    workshop_name = models.CharField(max_length=255)
    delete = models.BooleanField(default=False)
    
    def __str__(self):
        return self.workshop_name


class Payments_ID(models.Model):
    """Represents a method of payment"""
    payment_method_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=225)
    
    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Payment Method"
        verbose_name_plural = "Payment Methods"


class Clients(models.Model):
    """Represents a customer, storing contact info and lifetime value metrics."""
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
    
    def __str__(self):
        return self.name or self.phone or f"Client {self.client_id}"

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"


class Transactions(models.Model):
    """
    Represents a single customer transaction (a 'check' or 'receipt').
    """
    transaction_id = models.IntegerField(null=True, blank=True, unique=True)
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
    
    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"


class TransactionsProducts(models.Model):
    """
    Represents a single line item within a Transaction.
    This links a specific Product to a Transaction with quantity and price.
    """
    transaction = models.ForeignKey(Transactions, on_delete=models.CASCADE, related_name="products")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="transaction_entries")
    num = models.IntegerField(default=0)
    workshop = models.IntegerField(default=0)
    payed_sum = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    client = models.ForeignKey(Clients, on_delete=models.CASCADE, related_name="transaction_entries", null=True, blank=True)
    product_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    product_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        verbose_name = "Transaction Product"
        verbose_name_plural = "Transaction Products"


class TransactionHistory(models.Model):
    """
    Stores the audit trail or event log for a Transaction
    (e.g., 'open', 'close', 'payment_added').
    """
    transaction = models.ForeignKey(Transactions, on_delete=models.CASCADE, related_name="history")
    type_history = models.CharField(max_length=50)
    time = models.DateTimeField()
    value = models.CharField(default="")
    value2 = models.CharField(default="")
    value3 = models.CharField(default="")
    value_text = models.JSONField(null=True, blank=True)
    spot_tablet_id = models.IntegerField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Transaction History"
        verbose_name_plural = "Transaction Histories"


class AnalyticsRecord(models.Model):
    """
    Stores pre-aggregated analytics data for a specific date and entity type.
    This is used to cache complex calculations for the dashboard.
    """
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
    
    class Meta:
        verbose_name = "Analytics Record"
        verbose_name_plural = "Analytics Records"
        unique_together = ('type', 'entity_id', 'date')  


class CashShiftReport(models.Model):
    """
    Represents a single cash shift report (a 'Z-report' or 'end-of-day' summary)
    as reported by the external POS system.
    """
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
        return f"Shift {self.poster_shift_id} ({self.date_start.strftime('%Y-%m-%d')})"

    class Meta:
        verbose_name = "Cash Shift Report"
        verbose_name_plural = "Cash Shift Reports"



class ShiftSale(models.Model):
    """
    Stores the application's *own* calculated sales summary for a given shift,
    aggregating data from transactions and products.
    """
    shift_id = models.IntegerField()
    date = models.DateField()

    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    total_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    total_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    total_delivery_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    total_delivery_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    
    tips = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    
    class Meta:
        verbose_name = "Aggregated Shift Sale"
        verbose_name_plural = "Aggregated Shift Sales"


class ShiftSaleItem(models.Model):
    """
    Represents a single aggregated line item within a ShiftSale report.
    This is a denormalized model for fast reporting.
    """
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
    
    class Meta:
        verbose_name = "Aggregated Shift Item"
        verbose_name_plural = "Aggregated Shift Items"


class Spot(models.Model):
    """Represents a business location or 'spot' (e.g., 'Main Street Cafe')."""
    spot_id = models.IntegerField()
    spot_name = models.CharField(max_length=255, blank=True, null=True, default="") 
    spot_address = models.CharField(max_length=255, blank=True, null=True, default="")   
    
    def __str__(self):
        return self.spot_name or f"Spot {self.spot_id}"