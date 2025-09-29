from django.shortcuts import render
from rest_framework import generics, viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import (
    Employee, 
    Role, 
    User
    )
from .serializers import (
    EmployeeSerializer, 
    RegisterSerializer, 
    RoleSerializer,
    UserSerializer
    )



class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = []
    
    
class MeView(APIView):
        permission_classes = [IsAuthenticated]
        
        def get(self, request):
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer        