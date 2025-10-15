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
router.register(r'cash_shifts', CashShiftViewSet, basename='cashshift')
router.register(r'shift_sales', ShiftSalesView, basename='shift_sales')
router.register(r'transactions_history', TransactionsHistoryViewSet, basename='transactions_history')
router.register(r'payment-methods', PaymentMethodsView, basename='payment-methods')
router.register(r'poster_api_workshop', WorkshopViewSet, basename='workshop')
router.register(r'poster_api_product', ProductViewSet, basename='product')
router.register(r'spot', SpotViewSet, basename='spot')


urlpatterns = [
    path('', include(router.urls)),
]