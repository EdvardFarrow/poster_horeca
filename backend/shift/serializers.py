from rest_framework import serializers
from users.models import User
from .models import Shift, ShiftEmployee

class ShiftEmployeeSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.name", read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True)

    class Meta:
        model = ShiftEmployee
        fields = ["id", "employee", "employee_name", "role", "role_name"]


class ShiftSerializer(serializers.ModelSerializer):
    employees = ShiftEmployeeSerializer(source="shiftemployee_set", many=True, read_only=True)
    date = serializers.SerializerMethodField()

    class Meta:
        model = Shift
        fields = ["id", "poster_shift_id", "date_start", "date_end", "date", "employees"]