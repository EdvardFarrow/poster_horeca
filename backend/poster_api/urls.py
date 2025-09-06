from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CashShiftViewSet, PaymentMethodsView, StatisticsView, ShiftSalesView, TransactionsHistoryViewSet

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

transactions_router = DefaultRouter()
transactions_router.register(
    r'transactions_history', 
    TransactionsHistoryViewSet, 
    basename='transactions_history')

payment_router = DefaultRouter()
payment_router.register(
    r'payment-methods',
    PaymentMethodsView,
    basename='payment-methods'
)


urlpatterns = [
    path('', include(statistics_router.urls)),
    path('', include(reports_router.urls)),
    path('', include(shift_sales_router.urls)),
    path('', include(transactions_router.urls)),
    path('', include(payment_router.urls)),
]
