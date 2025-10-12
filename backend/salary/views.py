from collections import defaultdict
from decimal import Decimal
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from calendar import day_name
from rest_framework.permissions import IsAuthenticated
import logging


from .services import calculate_and_save_shift_salaries
from salary.aggreg import aggregate_sales
from shift.models import Shift
from poster_api.models import Employee
from .models import SalaryRecord, SalaryRule
from .serializers import  SalaryRecordSerializer, SalaryRuleSerializer

logger = logging.getLogger(__name__)


class SalaryRecordViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    
    queryset = SalaryRecord.objects.all()
    serializer_class = SalaryRecordSerializer

    def list(self, request, *args, **kwargs):
        try:
            year = int(request.query_params.get('year'))
            month = int(request.query_params.get('month'))
        except (TypeError, ValueError):
            return Response({"error": "Year and month must be provided."}, status=400)

        queryset = self.get_queryset().filter(
            shift__date__year=year,
            shift__date__month=month
        ).select_related('employee', 'shift')

        salaries_by_employee = defaultdict(dict)
        for calc in queryset:
            day_of_month = calc.shift.date.day
            emp_id = calc.employee_id
            
            salaries_by_employee[emp_id][day_of_month] = {
                "total_salary": calc.total_salary,
                "details": {
                    "fixed": calc.fixed_part,
                    "percent": calc.percent_part,
                    "bonus": calc.bonus_part,
                }
            }
        
        return Response(salaries_by_employee)



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
        
        
        
        
class SaveShiftSalaryViewSet(viewsets.ViewSet):
    queryset = Shift.objects.all()
    permission_classes = [IsAuthenticated] 

    @action(detail=True, methods=['post'], url_path='recalculate_salary')
    def recalculate_salary(self, request, pk=None):
        shift = self.get_object()
        
        calculate_and_save_shift_salaries(shift)
        
        return Response(
            {"status": "success", "message": f"Salary for shift {shift.id} recalculated."},
            status=status.HTTP_200_OK
        )        