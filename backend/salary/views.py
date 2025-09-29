# salary/views.py
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from calendar import day_name
from rest_framework.permissions import IsAuthenticated



from poster_api.client import PosterAPIClient
from .models import SalaryRecord, SalaryRule, SalaryRuleProduct
from .serializers import PosterEmployeeSerializer, SalaryRecordSerializer, SalaryRuleSerializer

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



class PosterEmployeesViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        client = PosterAPIClient()
        employees = client.get_employees()

        serializer = PosterEmployeeSerializer(employees, many=True)
        return Response(serializer.data)
    
    
    
class SalaryRuleViewSet(viewsets.ModelViewSet):
    queryset = SalaryRule.objects.all()
    serializer_class = SalaryRuleSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        salary_rule = serializer.save()

        workshops = request.data.get("workshops", [])
        if workshops:
            salary_rule.workshops.set(workshops)

        for pf in request.data.get("product_fixed", []):
            SalaryRuleProduct.objects.create(
                salary_rule=salary_rule,
                product_id=pf.get("product"),
                fixed=pf.get("fixed", 0)
            )

        headers = self.get_success_headers(serializer.data)
        return Response(self.get_serializer(salary_rule).data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        salary_rule = self.get_object()
        serializer = self.get_serializer(salary_rule, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        salary_rule = serializer.save()

        workshops = request.data.get("workshops", [])
        if workshops is not None:
            salary_rule.workshops.set(workshops)

        product_fixed = request.data.get("product_fixed", None)
        if product_fixed is not None:
            SalaryRuleProduct.objects.filter(salary_rule=salary_rule).delete()
            for pf in product_fixed:
                SalaryRuleProduct.objects.create(
                    salary_rule=salary_rule,
                    product_id=pf.get("product"),
                    fixed=pf.get("fixed", 0)
                )

        return Response(self.get_serializer(salary_rule).data)