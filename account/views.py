from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework import status
from .serializers import SingUpSerializer, UserSerializer

User = get_user_model()

# Frontend Views
def login_view(request):
    if request.method == 'POST':
        # Add login logic here
        pass
    return render(request, 'account/login.html')

def register_view(request):
    if request.method == 'POST':
        # Add registration logic here
        pass
    return render(request, 'account/register.html')

@login_required
def profile_view(request):
    return render(request, 'account/profile.html')

def logout_view(request):
    logout(request)
    return redirect('home')

# API Views
@api_view(['POST'])
def register(request):
    serializer = SingUpSerializer(data=request.data)
    if serializer.is_valid():
        if not User.objects.filter(email=serializer.validated_data['email']).exists():
            user = User.objects.create(
                first_name=serializer.validated_data['first_name'],
                last_name=serializer.validated_data['last_name'],
                email=serializer.validated_data['email'],
                username=serializer.validated_data['email'],
                password=make_password(serializer.validated_data['password'])
            )
            return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)
        return Response({'message': 'User already exists'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


