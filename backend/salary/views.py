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


class SalaryRecordViewSet(viewsets.ModelViewSet):
    """
    API endpoint for accessing and managing saved SalaryRecord entries.
    
    This ViewSet reads from and writes to the 'details' JSONField,
    ensuring all data (including bonus breakdowns, write-offs, etc.) 
    is handled correctly.
    """
    permission_classes = [IsAuthenticated]
    
    queryset = SalaryRecord.objects.all()
    serializer_class = SalaryRecordSerializer

    def list(self, request, *args, **kwargs):
        """
        Retrieves all salary records for a given month and year,
        formatted for the frontend salary table.
        """
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
                "id": calc.id,
                "total_salary": calc.total_salary,
                "details": calc.details 
            }
        
        return Response(salaries_by_employee)
    
    def partial_update(self, request, *args, **kwargs):
        """
        Handles manual updates to a SalaryRecord from the detail modal.
        Writes changes directly to the 'details' JSONField.
        """
        record = self.get_object()
        
        new_details = request.data.get('details', {})

        record.details = {**(record.details or {}), **new_details}
        
        fixed = Decimal(record.details.get('fixed', 0))
        percent = Decimal(record.details.get('percent', 0))
        bonus = Decimal(record.details.get('bonus', 0))
        write_off = Decimal(record.details.get('write_off', 0))
        record.total_salary = fixed + percent + bonus - write_off
        
        record.fixed_part = fixed
        record.percent_part = percent
        record.bonus_part = bonus
        record.write_off = write_off
        record.comment = record.details.get('comment', '')
        
        record.save()
        
        response_data = {
            "id": record.id,
            "total_salary": record.total_salary,
            "details": record.details 
        }
        return Response(response_data, status=status.HTTP_200_OK)
    
    
    @action(detail=False, methods=['post'])
    def recalculate(self, request):
        """
        Recalculates all salaries for a given month and year.
        
        This action calls the `calculate_and_save_shift_salaries` service
        for every shift in the specified month.
        """
        try:
            month = int(request.data.get('month'))
            year = int(request.data.get('year'))
        except (TypeError, ValueError):
            return Response(
                {"error": "Missing or invalid 'month' or 'year'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        logger.info(f"--- Salary recalculation started for {month}/{year} ---")

        shifts_to_recalculate = Shift.objects.filter(
            date__year=year,
            date__month=month,
        )

        if not shifts_to_recalculate.exists():
            logger.warning("--- No shifts found for recalculation ---")
            return Response(
                {"message": "No shifts found for this month."},
                status=status.HTTP_404_NOT_FOUND
            )

        processed_count = 0
        
        for shift in shifts_to_recalculate:
            try:
                calculate_and_save_shift_salaries(shift=shift)
                
                logger.info(f"Recalculating shift {shift.id} for {shift.date}")
                processed_count += 1
                
            except Exception as e:
                logger.error(f"ERROR recalculating shift {shift.id}: {e}")

        logger.info(f"--- Recalculation finished. Processed shifts: {processed_count} ---")
        return Response(
            {"message": f"Recalculation finished. Processed shifts: {processed_count}"},
            status=status.HTTP_200_OK
        )



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
    Aggregates data by shift and calculates salaries by rollers/employees.
    """
    permission_classes = [IsAuthenticated]

    def format_employee_salary(self, employee_data):
        """
        Brings data of one employee to a convenient format for the frontend
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
        Returns the aggregated salary for a specific shift.
        Example: GET /api/salary/aggregate_sales/shift/12/
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
        Returns the sum of payments for all shifts for the month.  
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
    """
    A ViewSet to provide actions for triggering salary calculations
    that are saved to the database.
    
    This is distinct from `SalaryAggregateViewSet`, which only performs
    on-the-fly calculations for preview.
    """
    queryset = Shift.objects.all()
    permission_classes = [IsAuthenticated] 

    @action(detail=True, methods=['post'], url_path='recalculate_salary')
    def recalculate_salary(self, request, pk=None):
        """
        Triggers the calculation and saving of salaries for a specific shift.

        This action calls the `calculate_and_save_shift_salaries` service,
        which runs the `aggregate_sales` logic and then updates or creates
        `SalaryRecord` entries for each employee on that shift.

        Args:
            request: The DRF request object.
            pk (int): The primary key of the `Shift` to recalculate.

        Returns:
            Response: A 200 response indicating success.
        """
        shift = self.get_object()
        
        calculate_and_save_shift_salaries(shift)
        
        return Response(
            {"status": "success", "message": f"Salary for shift {shift.id} recalculated."},
            status=status.HTTP_200_OK
        )        