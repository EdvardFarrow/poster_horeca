from decimal import Decimal
from rest_framework import serializers
from .models import (
    CategoriesSales, 
    ProductSales, 
    Product, 
    Category,
    ShiftSale,
    ShiftSaleItem,
    TransactionHistory,
    Transactions,
    TransactionsProducts,
    Clients
)


class CategoryModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "category_id", 
            "name"
            ]

class ProductModelSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        source='category',  # связывает с полем categor
        queryset=Category.objects.all()
    )
    class Meta:
        model = Product
        fields = [
            "product_id", 
            "product_name", 
            "category_id", 
            "cost", 
            "fiscal", 
            "workshop"
            ]

class ProductSalesModelSerializer(serializers.ModelSerializer):
    product = ProductModelSerializer(read_only=True)

    class Meta:
        model = ProductSales
        fields = [
            "product", 
            "product_profit", 
            "count"
            ]

class CategoriesSalesModelSerializer(serializers.ModelSerializer):
    category = CategoryModelSerializer(read_only=True)

    class Meta:
        model = CategoriesSales
        fields = [
            "category_id",
            "category_name",
            "profit", 
            "count"
            ]


class ProductAPISerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    category_id = serializers.IntegerField()
    category_name = serializers.CharField()
    cost = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    fiscal = serializers.BooleanField(default=True)
    workshop = serializers.IntegerField(default=0)

class ProductSalesAPISerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    category_id = serializers.IntegerField()
    category_name = serializers.CharField()
    product_price = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    count = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    product_profit = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)

class CategoryAPISerializer(serializers.Serializer):
    category_id = serializers.IntegerField()
    name = serializers.CharField()

class CategoriesSalesAPISerializer(serializers.Serializer):
    category_id = serializers.IntegerField()
    name = serializers.CharField()
    count = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    profit = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)


class WorkshopSerializer(serializers.Serializer):
    workshop_id = serializers.IntegerField()
    workshop_name = serializers.CharField(max_length=255)
    delete = serializers.BooleanField(default=False)


class PaymentMethodSerializer(serializers.Serializer):
    payment_method_id = serializers.IntegerField()
    title = serializers.CharField(max_length=255)


class TransactionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transactions
        fields = "__all__"
        
class TransactionsProductsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionsProducts
        field = "__all__"        

class TransactionHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionHistory
        fields = "__all__"


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clients
        fields = [
            "client_id",
            "firstname",
            "lastname",
            "name",
            "phone",
            "email",
            "revenue",
            "profit",
            "transactions",
        ]






class EmployeeSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField(source="id")
    employee_name = serializers.CharField(source="name")




class CashShiftSerializer(serializers.Serializer):
    poster_shift_id = serializers.CharField()
    date_start = serializers.CharField()
    date_end = serializers.CharField()
    amount_start = serializers.FloatField()
    amount_end = serializers.FloatField()
    amount_debit = serializers.FloatField()
    amount_sell_cash = serializers.FloatField()
    amount_sell_card = serializers.FloatField()
    amount_credit = serializers.FloatField()
    amount_collection = serializers.FloatField  ()
    user_id_start = serializers.CharField(allow_null=True, allow_blank=True)
    user_id_end = serializers.CharField(allow_null=True, allow_blank=True)
    comment = serializers.CharField(allow_null=True, allow_blank=True)




# class TransactionHistorySerializer(serializers.Serializer):
#     transaction_id = serializers.CharField()
#     type_history = serializers.CharField()
#     time = serializers.CharField()
#     value = serializers.CharField(allow_null=True)
#     value2 = serializers.CharField(allow_null=True)
#     value3 = serializers.CharField(allow_null=True)
#     value_text = serializers.CharField(allow_null=True)
#     spot_tablet_id = serializers.CharField(allow_null=True)





class ShiftSaleItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=False, allow_null=True)
    product_name = serializers.CharField(allow_blank=True, required=False)
    count = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    product_sum = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    payed_sum = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    profit = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    workshop = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    delivery_service = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    tips = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)


class ShiftSalesSerializer(serializers.Serializer):
    regular = ShiftSaleItemSerializer(many=True)
    delivery = ShiftSaleItemSerializer(many=True)
    difference = serializers.DecimalField(max_digits=12, decimal_places=2)
    tips = serializers.DecimalField(max_digits=12, decimal_places=2)
    tips_by_service = serializers.DictField(child=serializers.DecimalField(max_digits=12, decimal_places=2))