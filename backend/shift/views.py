from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, timezone as dt_timezone
from .models import Shift, ShiftEmployee
from .serializers import ShiftSerializer
from users.models import Employee, Role

class ShiftViewSet(viewsets.ModelViewSet):
    queryset = Shift.objects.all().order_by("-date_start")
    serializer_class = ShiftSerializer

    @action(detail=False, methods=["post"], url_path="save_month")
    def save_month(self, request):
        
        data = request.data.get("shifts", [])
        created = 0

        for item in data:
            emp_id = item.get("employee")
            date_str = item.get("date")
            if not (emp_id and date_str):
                continue

            try:
                employee = Employee.objects.get(id=emp_id)
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

                shift, _ = Shift.objects.get_or_create(
                    date_start__date=date_obj,
                    defaults={
                        "poster_shift_id": f"manual-{date_obj}",
                        "date_start": datetime.combine(date_obj, datetime.min.time(), tzinfo=dt_timezone.utc),
                        "date_end": datetime.combine(date_obj, datetime.max.time(), tzinfo=dt_timezone.utc),
                    },
                )

                if not shift:
                    shift = Shift.objects.create(
                        poster_shift_id=f"manual-{date_obj}",
                        date_start=datetime.combine(date_obj, datetime.min.time()).astimezone(timezone.utc),
                        date_end=datetime.combine(date_obj, datetime.max.time()).astimezone(timezone.utc),
                    )

                if not ShiftEmployee.objects.filter(shift=shift, employee=employee).exists():
                    ShiftEmployee.objects.create(
                        shift=shift,
                        employee=employee,
                        role=employee.role  
                    )
                    created += 1

            except Employee.DoesNotExist:
                continue

        return Response(
            {"status": "ok", "created": created},
            status=status.HTTP_201_CREATED
        )
