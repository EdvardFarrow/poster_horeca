from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CashShiftViewSet, StatisticsView

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
    basename='cashshift')

urlpatterns = [
    path('', include(statistics_router.urls)),
    path('', include(reports_router.urls)),
]
