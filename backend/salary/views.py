# salary/views.py
from collections import defaultdict
from decimal import Decimal
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from calendar import day_name
from rest_framework.permissions import IsAuthenticated
import logging


from salary.aggreg import aggregate_sales
from shift.models import Shift
from poster_api.models import Employee
from .models import SalaryRecord, SalaryRule
from .serializers import  SalaryRecordSerializer, SalaryRuleSerializer

logger = logging.getLogger(__name__)


class SalaryRecordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SalaryRecord.objects.all()
    serializer_class = SalaryRecordSerializer
    permission_classes = [IsAuthenticated]

    def format_record(self, record):
        shift = record.shift
        return {
            "date": shift.date,
            "weekday": day_name[shift.date.weekday()],
            "fixed_rate": getattr(record, "fixed_income", 0),
            "percent_income": getattr(record, "percent_income", 0),
            "total_income": record.amount,
        }

    @action(detail=False, methods=["get"])
    def current(self, request):
        user = request.user
        today = timezone.now().date()
        records = SalaryRecord.objects.filter(
            employee=user,
            shift__date__year=today.year,
            shift__date__month=today.month
        )
        formatted = [self.format_record(r) for r in records]
        total = sum(r.amount for r in records)
        return Response({
            "month": today.month,
            "year": today.year,
            "shifts": formatted,
            "total_income": total
        })

    @action(detail=False, methods=["get"], url_path="archive/(?P<year>\\d+)/(?P<month>\\d+)")
    def archive(self, request, year=None, month=None):
        user = request.user
        records = SalaryRecord.objects.filter(
            employee=user,
            shift__date__year=year,
            shift__date__month=month
        )
        formatted = [self.format_record(r) for r in records]
        total = sum(r.amount for r in records)
        return Response({
            "month": int(month),
            "year": int(year),
            "shifts": formatted,
            "total_income": total
        })




    
    
    
class SalaryRuleViewSet(viewsets.ModelViewSet):
    queryset = SalaryRule.objects.all()
    serializer_class = SalaryRuleSerializer
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        salary_rule = self.get_object()
        salary_rule.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    


class SalaryAggregateViewSet(viewsets.ViewSet):
    """
    Агрегирует данные по сменам и рассчитывает зарплату по ролям/сотрудникам.
    """
    permission_classes = [IsAuthenticated]

    def format_employee_salary(self, employee_data):
        """
        Приводит данные одного сотрудника к удобному формату для фронта
        """
        emp = employee_data["employee"]
        total = employee_data["total_salary"]

        return {
            "employee_id": emp.id,
            "employee_name": emp.name,
            "role_name": emp.role.name if hasattr(emp, "role") and emp.role else None,
            "additional": float(total),
        }

    @action(detail=False, methods=["get"], url_path=r"shift/(?P<shift_id>\d+)")
    def by_shift(self, request, shift_id=None):
        """
        Возвращает агрегированную зарплату по конкретной смене.
        Пример: GET /api/salary/aggregate_sales/shift/12/
        """
        try:
            shift = Shift.objects.get(id=shift_id)
        except Shift.DoesNotExist:
            return Response({"error": "Смена не найдена"}, status=404)

        logger.info(f"Агрегация зарплаты для смены ID={shift_id}")

        result = aggregate_sales(shift)

        formatted = [self.format_employee_salary(v) for v in result.values()]
        total = sum(v["additional"] for v in formatted)

        return Response({
            "shift_id": shift.id,
            "date": shift.date if hasattr(shift, "date") else None,
            "employees": formatted,
            "total_shift_payout": total
        })

    @action(detail=False, methods=["get"], url_path=r"month/(?P<year>\d{4})/(?P<month>\d{1,2})")
    def by_month(self, request, year=None, month=None):
        """
        Возвращает сумму выплат по всем сменам за месяц.
        """
        shifts = Shift.objects.filter(date__year=year, date__month=month)
        if not shifts.exists():
            return Response({"error": "Смены за указанный месяц не найдены"}, status=404)

        logger.info(f"Агрегация зарплаты за {month}.{year}")

        total_result = defaultdict(Decimal)
        for shift in shifts:
            result = aggregate_sales(shift)
            for emp_id, data in result.items():
                total_result[emp_id] += data["total_salary"]

        employees = Employee.objects.filter(id__in=total_result.keys())

        formatted = [
            {
                "employee_id": emp.id,
                "employee_name": emp.name,
                "total_month_salary": float(total_result[emp.id])
            }
            for emp in employees
        ]

        return Response({
            "year": int(year),
            "month": int(month),
            "employees": formatted,
            "total": sum(e["total_month_salary"] for e in formatted)
        })