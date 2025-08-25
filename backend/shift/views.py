from datetime import date
from calendar import monthrange
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import PlannedShift, ShiftParticipation, Shift
from .serializers import PlannedShiftSerializer, ShiftParticipationSerializer, ShiftSerializer

class PlannedShiftViewSet(viewsets.ModelViewSet):
    queryset = PlannedShift.objects.all().order_by('date', 'planned_start_time')
    serializer_class = PlannedShiftSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'date']  

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save()  


    @action(detail=False, methods=['get'])
    def by_month(self, request):
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        weeks = request.query_params.getlist('weeks')

        if not (year and month):
            return Response({"detail": "Укажите Год и Месяц"}, status=400)

        try:
            year = int(year)
            month = int(month)
            start_date = date(year, month, 1)
            end_date = date(year, month, monthrange(year, month)[1])
        except ValueError:
            return Response({"detail": "Некорректный формат Год или Месяц"}, status=400)

        qs = self.queryset.filter(date__gte=start_date, date__lte=end_date)
            
            
        if weeks:
            filtered_qs = []
            for shift in qs:
                day_of_month = shift.date.day
                week_number = (day_of_month - 1) // 7 + 1
                if str(week_number) in weeks:
                    filtered_qs.append(shift)
            qs = filtered_qs
            
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_week(self, request):
        start_date_str = request.query_params.get('start')
        end_date_str = request.query_params.get('end')

        if not (start_date_str and end_date_str):
            return Response({"detail": "Укажите start и end даты"}, status=400)

        try:
            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)
        except ValueError:
            return Response({"detail": "Некорректный формат даты. Используйте YYYY-MM-DD."}, status=400)

        qs = self.queryset.filter(date__gte=start_date, date__lte=end_date)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)



class ShiftViewSet(viewsets.ModelViewSet):
    """
    API для управления фактическими сменами.
    CRUD-операции отключены. Используется для GET и внесения факта участия.
    """
    queryset = Shift.objects.all().order_by('-date')
    serializer_class = ShiftSerializer
    permission_classes = [permissions.IsAuthenticated] 

    # Запрещаем базовые операции POST, PUT, DELETE
    http_method_names = ['get', 'patch']     
    
    # Получить ПЛАН на сегодня (остается без изменений)
    # GET /api/shifts/suggested_participants/?date=YYYY-MM-DD
    @action(detail=False, methods=['get'])
    def suggested_participants(self, request):
        """
        Предлагает список участников из PlannedShift для указанной даты.
        """
        target_date_str = request.query_params.get('date')
        
        if not target_date_str:
            return Response({"detail": "Необходимо указать дату в параметре 'date'."}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        try:
            target_date = date.fromisoformat(target_date_str)
        except ValueError:
            return Response({"detail": "Некорректный формат даты. Используйте YYYY-MM-DD."}, 
                            status=status.HTTP_400_BAD_REQUEST)

        planned_shifts = PlannedShift.objects.filter(date=target_date)
        
        if not planned_shifts.exists():
            return Response({"detail": "На эту дату не найдено запланированных смен."}, 
                            status=status.HTTP_404_NOT_FOUND)

        serializer = PlannedShiftSerializer(planned_shifts, many=True)
        return Response(serializer.data)


    # Внесение/Корректировка ФАКТИЧЕСКИХ участников
    # PATCH /api/shifts/{pk}/correct_participation/
    @action(detail=True, methods=['patch'])
    @transaction.atomic 
    def correct_participation(self, request, pk=None):
        shift = get_object_or_404(Shift, pk=pk)

        # Ожидаем список участников от фронтенда
        participants_data = request.data.get('participants', [])
        
        if not participants_data:
            return Response({"detail": "Необходимо передать данные фактических участников (participants)."}, 
                            status=status.HTTP_400_BAD_REQUEST)

        # Валидация фактических участников (ShiftParticipationSerializer)
        participants_serializer = ShiftParticipationSerializer(data=participants_data, many=True)
        participants_serializer.is_valid(raise_exception=True)

        # Очищаем старые данные об участии для этой смены
        ShiftParticipation.objects.filter(shift=shift).delete()
        
        # Создаем фактические записи об участии (ShiftParticipation)
        for data in participants_serializer.validated_data:
            ShiftParticipation.objects.create(shift=shift, **data)

        shift.save() 
        
        return Response(self.get_serializer(shift).data, status=status.HTTP_200_OK)