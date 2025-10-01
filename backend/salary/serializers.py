from rest_framework import serializers

from poster_api.models import Product, Workshop
from poster_api.serializers import WorkshopSerializer
from .models import SalaryRule, SalaryRecord, SalaryRuleProduct



class SalaryRuleProductSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product_obj'
    )

    def to_internal_value(self, data):
        try:
            product_obj = Product.objects.get(product_id=data['product'] if isinstance(data, dict) else data)
        except Product.DoesNotExist:
            raise serializers.ValidationError(f"Product with product_id={data} does not exist")
        return {
            'product_obj': product_obj,
            'fixed': data['fixed'] if isinstance(data, dict) else 0
        }

    class Meta:
        model = SalaryRuleProduct
        fields = ["product", "fixed"]


class SalaryRuleSerializer(serializers.ModelSerializer):
    workshops = serializers.PrimaryKeyRelatedField(queryset=Workshop.objects.all(), many=True)
    product_fixed = SalaryRuleProductSerializer(many=True, write_only=True, required=False)
    role_name = serializers.CharField(source="role.name", read_only=True)

    class Meta:
        model = SalaryRule
        fields = "__all__"

    def create(self, validated_data):
        product_fixed_data = validated_data.pop("product_fixed", [])
        workshops = validated_data.pop("workshops", [])

        salary_rule = SalaryRule.objects.create(**validated_data)
        salary_rule.workshops.set(workshops)

        for pf in product_fixed_data:
            SalaryRuleProduct.objects.create(
                salary_rule=salary_rule,
                product=pf['product_obj'],
                fixed=pf['fixed']
            )

        return salary_rule

    def update(self, instance, validated_data):
        product_fixed_data = validated_data.pop("product_fixed", None)
        workshops = validated_data.pop("workshops", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if workshops is not None:
            instance.workshops.set(workshops)

        if product_fixed_data is not None:
            instance.salaryruleproduct_set.all().delete()
            for pf in product_fixed_data:
                SalaryRuleProduct.objects.create(
                    salary_rule=instance,
                    product=pf['product_obj'],
                    fixed=pf['fixed']
                )

        return instance





class SalaryRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryRecord
        fields = '__all__'


class PosterEmployeeSerializer(serializers.Serializer):
    poster_id = serializers.IntegerField()
    name = serializers.CharField()
    role_id = serializers.IntegerField(required=False, allow_null=True)
    role_name = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    access_mask = serializers.IntegerField(required=False, allow_null=True)
    user_type = serializers.IntegerField(required=False, allow_null=True)
    last_in = serializers.CharField(required=False, allow_blank=True)