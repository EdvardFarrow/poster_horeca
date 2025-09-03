from rest_framework import serializers



class FinanceSerializer(serializers.Serializer):
    sum = serializers.DecimalField(max_digits=12, decimal_places=2)
    profit = serializers.DecimalField(max_digits=12, decimal_places=2)
    orders_count = serializers.IntegerField()



class SalesSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    category_id = serializers.IntegerField()
    category_name = serializers.CharField()
    sum = serializers.DecimalField(max_digits=12, decimal_places=2)
    count = serializers.IntegerField()


class ProductSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    payed_sum = serializers.DecimalField(max_digits=12, decimal_places=2)
    count = serializers.DecimalField(max_digits=12, decimal_places=2)
    price = serializers.DecimalField(max_digits=12, decimal_places=2, source="product_sum")
    profit = serializers.DecimalField(max_digits=12, decimal_places=2)
    workshop = serializers.IntegerField()
    
class ShiftSalesSerializer(serializers.Serializer):
    shift_id = serializers.IntegerField()
    regular = ProductSerializer(many=True)
    delivery = ProductSerializer(many=True)    


class CategorySerializer(serializers.Serializer):
    category_id = serializers.IntegerField()
    category_name = serializers.CharField()
    sum = serializers.DecimalField(max_digits=12, decimal_places=2)
    count = serializers.IntegerField()


class ClientSerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.CharField(required=False, allow_null=True)
    visits = serializers.IntegerField(source="transactions")
    sum = serializers.DecimalField(max_digits=12, decimal_places=2, source="revenue")
    avg_check = serializers.DecimalField(max_digits=12, decimal_places=2)


class EmployeeSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField(source="id")
    employee_name = serializers.CharField(source="name")
    orders_count = serializers.IntegerField(source="transactions")
    sum = serializers.DecimalField(max_digits=12, decimal_places=2, source="revenue")
    avg_check = serializers.DecimalField(max_digits=12, decimal_places=2)

class DiscountSerializer(serializers.Serializer):
    discount_id = serializers.IntegerField()
    discount_name = serializers.CharField()
    sum = serializers.DecimalField(max_digits=12, decimal_places=2)
    count = serializers.IntegerField()


class DepartmentSerializer(serializers.Serializer):
    department_id = serializers.IntegerField()
    department_name = serializers.CharField()
    sum = serializers.DecimalField(max_digits=12, decimal_places=2)
    orders_count = serializers.IntegerField()



class RevenueProfitSerializer(serializers.Serializer):
    name = serializers.CharField()
    count = serializers.FloatField(required=False)
    revenue = serializers.FloatField(required=False)
    profit = serializers.FloatField(required=False)
    product_profit = serializers.FloatField(required=False)






class StatisticsResponseSerializer(serializers.Serializer):
    type = serializers.CharField()
    data = serializers.ListField()

    def to_representation(self, instance):
        type_ = instance.get("type")
        data = instance.get("data", [])

        # Приведение к списку на случай, если пришёл один объект
        if isinstance(data, dict):
            data = [data]

        if type_ == "products":
            serialized_data = [
                {
                    "product_name": item.get("name", ""),
                    "count": float(item.get("count", 0)),
                    "product_profit": float(item.get("product_profit", 0)),
                }
                for item in data
            ]
        elif type_ == "categories":
            serialized_data = [
                {
                    "category_name": item.get("name", ""),
                    "count": float(item.get("count", 0)),
                    "profit": float(item.get("profit", 0)),
                }
                for item in data
            ]
        elif type_ == "waiters":
            serialized_data = [
                {
                    "employee_name": item.get("name", ""),
                    "orders_count": int(item.get("transactions", 0)),
                    "sum": float(item.get("revenue", 0)),
                    "avg_check": float(item.get("avg_check", 0)),
                    "profit": float(item.get("profit", 0)),
                }
                for item in data
            ]
        elif type_ == "clients":
            serialized_data = [
                {
                    "name": item.get("name", ""),
                    "email": item.get("email"),
                    "visits": int(item.get("transactions", 0)),
                    "sum": float(item.get("revenue", 0)),
                    "avg_check": float(item.get("avg_check", 0)),
                }
                for item in data
            ]
        elif type_ == "workshops":
            serialized_data = [
                {
                    "department_name": item.get("name", ""),
                    "sum": round(int(item.get("sum", 0)) / 100, 2),
                    "orders_count": int(item.get("count", 0)),
                    "profit": round(int(item.get("profit", 0)) / 100, 2),
                }
                for item in data
            ]    
        else:
            # Для остальных типов просто возвращаем данные как есть
            serialized_data = data

        return {
            "type": type_,
            "data": serialized_data
        }




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
