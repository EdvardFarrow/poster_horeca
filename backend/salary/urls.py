from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PosterEmployeesViewSet, SalaryRuleViewSet, SalaryRecordViewSet

rules_router = DefaultRouter()
rules_router.register(r'rules', SalaryRuleViewSet, basename='salary-rule')

records_router = DefaultRouter()
records_router.register(r'records', SalaryRecordViewSet, basename='salary-record')

employees_router = DefaultRouter()
employees_router.register(r'employees', PosterEmployeesViewSet, basename='poster-employee')

urlpatterns = [
    path('', include(rules_router.urls)),
    path('', include(records_router.urls)),
    path('', include(employees_router.urls)),
]
