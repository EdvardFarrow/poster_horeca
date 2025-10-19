from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView
)
from .views import (
    #RegisterView, 
    UserViewSet, 
    MeView,
    EmployeeViewSet,
    RoleViewSet
    )

from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

emp_role_router = DefaultRouter()
emp_role_router.register(r'employee', EmployeeViewSet, basename='employee')
emp_role_router.register(r'role', RoleViewSet, basename='role')




urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('register/', RegisterView.as_view(), name='auth_register'),
    path('logout/', TokenBlacklistView.as_view(), name='logout'),
    path("user/", MeView.as_view(), name="user"),
    path('', include(router.urls)),
    path('', include(emp_role_router.urls)),
]