from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Shift, ShiftEmployee
from poster_api.models import ShiftSale
from .serializers import ShiftSerializer
from users.models import Employee
from datetime import datetime

class ShiftViewSet(viewsets.ModelViewSet):
    queryset = Shift.objects.all().order_by("-date")
    serializer_class = ShiftSerializer

    @action(detail=False, methods=["post"], url_path="save_month")
    def save_month(self, request):
        data = request.data.get("shifts", [])
        created_count = 0
        updated_count = 0

        for item in data:
            emp_ids = item.get("employees", [])
            date_str = item.get("date")
            if not date_str:
                continue

            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                continue

            poster_shift = ShiftSale.objects.filter(date=date_obj).first()
            if poster_shift:
                poster_shift_id = str(poster_shift.shift_id)
            else:
                poster_shift_id = str(date_obj)  

            shift, created_shift = Shift.objects.update_or_create(
                shift_id=poster_shift_id,
                defaults={"date": date_obj},
            )

            if created_shift:
                created_count += 1
            else:
                updated_count += 1

            for emp_id in emp_ids:
                try:
                    employee = Employee.objects.get(id=emp_id)
                    ShiftEmployee.objects.update_or_create(
                        shift=shift,
                        employee=employee,
                        defaults={"role": employee.role},
                    )
                except Employee.DoesNotExist:
                    continue

            ShiftEmployee.objects.filter(shift=shift).exclude(employee_id__in=emp_ids).delete()

        return Response(
            {
                "status": "ok",
                "shifts_created": created_count,
                "shifts_updated": updated_count
            },
            status=status.HTTP_201_CREATED
        )

    def list(self, request, *args, **kwargs):
        month = int(request.query_params.get("month"))
        year = int(request.query_params.get("year"))

        shifts = Shift.objects.filter(date__year=year, date__month=month).prefetch_related("employees")
        result = []

        for shift in shifts:
            emp_ids = list(shift.employees.values_list("id", flat=True))
            result.append({
                "date": shift.date.strftime("%Y-%m-%d"),
                "employees": emp_ids
            })

        return Response(result)