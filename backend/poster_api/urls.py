from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CashShiftViewSet, StatisticsView, ShiftSalesView

statistics_router = DefaultRouter()
statistics_router.register(
    r'statistics',
    StatisticsView,
    basename='statistics'
)

reports_router = DefaultRouter()
reports_router.register(
    r'cash_shifts',
    CashShiftViewSet,
    basename='cashshift'
)

shift_sales_router = DefaultRouter()
shift_sales_router.register(
    r'shift_sales',
    ShiftSalesView,
    basename='shift_sales'
)


urlpatterns = [
    path('', include(statistics_router.urls)),
    path('', include(reports_router.urls)),
    path('', include(shift_sales_router.urls)),
]
