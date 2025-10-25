from rest_framework import serializers
from .models import PayGroup, User, Employee, Role

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'fullname', 'password', 'role']
        extra_kwargs = {
            'role': {'required': False} 
        }

    # method create for hash password
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            fullname=validated_data['fullname'],
            role=validated_data.get('role', 'employee') 
        )
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'fullname', 'role']


class RoleSerializer(serializers.ModelSerializer):
    pay_group_name = serializers.CharField(source='pay_group.name', read_only=True)

    class Meta:
        model = Role
        fields = (
            'id', 
            'name', 
            'description', 
            'pay_group', 
            'pay_group_name' 
        )

class EmployeeSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="role.name", read_only=True)

    class Meta:
        model = Employee
        fields = ["id", "name", "role", "role_name", "is_active"]
        
        
class PayGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayGroup
        fields = ('id', 'name')        