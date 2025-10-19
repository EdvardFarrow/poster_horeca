from rest_framework import serializers

from poster_api.models import Product, Workshop
from poster_api.serializers import WorkshopSerializer
from .models import SalaryRule, SalaryRecord, SalaryRuleProduct



class SalaryRuleProductSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.product_name', read_only=True)

    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())


    class Meta:
        model = SalaryRuleProduct
        fields = [
            'product',         
            'product_name',    
            'fixed',           
        ]
        read_only_fields = ['product_name']


class SalaryRuleSerializer(serializers.ModelSerializer):
    workshops = serializers.PrimaryKeyRelatedField(queryset=Workshop.objects.all(), many=True)
    role_name = serializers.CharField(source="role.name", read_only=True)

    product_fixed = SalaryRuleProductSerializer(
        source='salaryruleproduct_set',
        many=True, 
        required=False
    )
    
    class Meta:
        model = SalaryRule
        fields = [
            'id',
            'role',
            'role_name',
            'workshops',
            'percent',
            'fixed_per_shift',
            'product_fixed' 
        ]

    def create(self, validated_data):
        product_fixed_data = validated_data.pop("salaryruleproduct_set", [])
        workshops = validated_data.pop("workshops", [])

        salary_rule = SalaryRule.objects.create(**validated_data)
        salary_rule.workshops.set(workshops)

        for pf in product_fixed_data:
            SalaryRuleProduct.objects.create(
                salary_rule=salary_rule,
                product=pf['product'], 
                fixed=pf['fixed']
            )
        return salary_rule

    def update(self, instance, validated_data):
        product_fixed_data = validated_data.pop("salaryruleproduct_set", None)
        workshops = validated_data.pop("workshops", None)

        instance.role = validated_data.get('role', instance.role)
        instance.percent = validated_data.get('percent', instance.percent)
        instance.fixed_per_shift = validated_data.get('fixed_per_shift', instance.fixed_per_shift)
        instance.save()

        if workshops is not None:
            instance.workshops.set(workshops)

        if product_fixed_data is not None:
            instance.salaryruleproduct_set.all().delete() 
            for pf in product_fixed_data:
                SalaryRuleProduct.objects.create(
                    salary_rule=instance,
                    product=pf['product'],
                    fixed=pf['fixed']
                )
        return instance



class SalaryRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryRecord
        fields = [
            'total_salary', 
            'fixed_part', 
            'percent_part', 
            'bonus_part'
        ]


