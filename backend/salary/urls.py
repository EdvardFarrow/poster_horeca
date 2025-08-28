from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SalaryRuleViewSet, SalaryRecordViewSet, RecalculateSalaryView

router = DefaultRouter()
router.register(r'rules', SalaryRuleViewSet, basename='salary-rule')
router.register(r'records', SalaryRecordViewSet, basename='salary-record')

urlpatterns = [
    path('', include(router.urls)),
    path('recalculate/<int:shift_id>/', RecalculateSalaryView.as_view(), name='salary-recalculate'),
]
