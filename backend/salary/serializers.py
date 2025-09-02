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


class PosterEmployeeSerializer(serializers.Serializer):
    poster_id = serializers.IntegerField()
    name = serializers.CharField()
    role_id = serializers.IntegerField(required=False, allow_null=True)
    role_name = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    access_mask = serializers.IntegerField(required=False, allow_null=True)
    user_type = serializers.IntegerField(required=False, allow_null=True)
    last_in = serializers.CharField(required=False, allow_blank=True)