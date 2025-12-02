from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CashShiftViewSet,
    PaymentMethodsView,
    ProductViewSet,
    ShiftSalesView,
    TransactionsHistoryViewSet,
    WorkshopViewSet,
    SpotViewSet
)

router = DefaultRouter()
router.register(r'cash_shifts', CashShiftViewSet, basename='cash_shift')
router.register(r'shift_sales', ShiftSalesView, basename='shift_sales')
router.register(r'transactions', TransactionsHistoryViewSet, basename='transactions')
router.register(r'payment_methods', PaymentMethodsView, basename='payment_methods')
router.register(r'workshop', WorkshopViewSet, basename='workshop')
router.register(r'products', ProductViewSet, basename='products')
router.register(r'spots', SpotViewSet, basename='spots')


urlpatterns = [
    path('', include(router.urls)),
]