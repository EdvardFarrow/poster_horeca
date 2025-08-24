from django.shortcuts import render
from rest_framework import generics, viewsets
from .models import User
from .serializers import RegisterSerializer, UserSerializer 

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = []