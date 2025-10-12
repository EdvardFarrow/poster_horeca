from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SalaryRuleViewSet, SalaryRecordViewSet, SalaryAggregateViewSet, SaveShiftSalaryViewSet

router = DefaultRouter()
router.register(r'salary_rules', SalaryRuleViewSet, basename='salary_rules')
router.register(r'salary_records', SalaryRecordViewSet, basename='salary_records')
router.register(r'aggregate_sales', SalaryAggregateViewSet, basename='aggregate_sales')
router.register(r'save_shift_salary', SaveShiftSalaryViewSet, basename='save_shift_salary')


urlpatterns = [
    path('', include(router.urls)),
]
