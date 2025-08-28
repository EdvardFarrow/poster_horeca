from rest_framework import serializers
from .models import SalaryRule, SalaryRecord

class SalaryRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryRule
        fields = '__all__'


class SalaryRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryRecord
        fields = '__all__'
