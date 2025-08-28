from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AnalyticsView

router = DefaultRouter()
router.register(
    r'analytics',
    AnalyticsView,
    basename='analytics'
)

urlpatterns = [
    path('', include(router.urls)),
]
