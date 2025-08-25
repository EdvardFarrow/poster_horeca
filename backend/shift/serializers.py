from rest_framework import serializers
from users.models import User
from .models import Shift, ShiftParticipation, PlannedShift

class UserShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "fullname", "role"]


class ShiftParticipationSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)  
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source="user"
    )

    class Meta:
        model = ShiftParticipation
        fields = ["id", "user", "user_id", "role", "check_in_time", "check_out_time"]


class ShiftSerializer(serializers.ModelSerializer):
    participants = ShiftParticipationSerializer(source="shiftparticipation_set", many=True, read_only=True)

    class Meta:
        model = Shift
        fields = [
            "id", "date", "start_time", "end_time",
            "status", "participants", "created_by"
        ]


class PlannedShiftSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        write_only=True, 
        source="user" 
    )
    
    user = UserShortSerializer(read_only=True)
    
    created_by = UserShortSerializer(read_only=True) 

    class Meta:
        model = PlannedShift
        fields = [
            "id", "date", "role", 
            "planned_start_time", "planned_end_time", 
            "user", "user_id", "created_by"
        ]
        # Поле created_by_id не нужно, так как его, вероятно, будем 
        # заполнять автоматически во View на основе request.user
        read_only_fields = ['created_by']
