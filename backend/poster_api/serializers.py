from rest_framework import serializers


class FinanceSerializer(serializers.Serializer):
    sum = serializers.DecimalField(max_digits=12, decimal_places=2)
    cost = serializers.DecimalField(max_digits=12, decimal_places=2)
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
    sum = serializers.DecimalField(max_digits=12, decimal_places=2)
    count = serializers.IntegerField()


class CategorySerializer(serializers.Serializer):
    category_id = serializers.IntegerField()
    category_name = serializers.CharField()
    sum = serializers.DecimalField(max_digits=12, decimal_places=2)
    count = serializers.IntegerField()


class ClientSerializer(serializers.Serializer):
    client_id = serializers.IntegerField()
    client_name = serializers.CharField(required=False, allow_null=True)
    visits = serializers.IntegerField()
    sum = serializers.DecimalField(max_digits=12, decimal_places=2)
    avg_check = serializers.DecimalField(max_digits=12, decimal_places=2)


class EmployeeSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField()
    employee_name = serializers.CharField()
    orders_count = serializers.IntegerField()
    sum = serializers.DecimalField(max_digits=12, decimal_places=2)
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


class AnalyticsResponseSerializer(serializers.Serializer):
    
    type = serializers.CharField()
    data = serializers.ListField()

    def to_representation(self, instance):
        type_ = instance.get("type")
        data = instance.get("data", [])

        serializer_class_map = {
            "finance": FinanceSerializer,
            "sales": SalesSerializer,
            "products": ProductSerializer,
            "categories": CategorySerializer,
            "clients": ClientSerializer,
            "employees": EmployeeSerializer,
            "discounts": DiscountSerializer,
            "departments": DepartmentSerializer,
        }

        serializer_class = serializer_class_map.get(type_)
        if serializer_class:
            serialized_data = serializer_class(data, many=True).data
        else:
            serialized_data = data

        return {
            "type": type_,
            "data": serialized_data
        }
