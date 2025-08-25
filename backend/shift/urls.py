from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlannedShiftViewSet, ShiftViewSet

router = DefaultRouter()

router.register(
    r'planned-shifts', 
    PlannedShiftViewSet, 
    basename='planned-shift' 
)

router.register(
    r'shifts', 
    ShiftViewSet, 
    basename='shift' 
)

urlpatterns = [
    path('', include(router.urls)),
]