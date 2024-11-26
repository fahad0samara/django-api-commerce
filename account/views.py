from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework import status
from .serializers import SingUpSerializer, UserSerializer

User = get_user_model()

@api_view(['GET'])
def api_root(request):
    return Response({
        'register': '/api/register/',
        'login': '/api/token/',
        'user_info': '/api/userinfo/',
        'available_endpoints': [
            '/api/register/',
            '/api/token/',
            '/api/userinfo/',
            '/products/',
            '/orders/',
            '/support/'
        ]
    })

@api_view(['POST'])
def register(request):
    serializer = SingUpSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        if not User.objects.filter(email=data['email']).exists():
            user = User.objects.create(
                first_name=data['first_name'],
                last_name=data['last_name'],
                email=data['email'],
                username=data['email'],
                password=make_password(data['password'])
            )
            return Response(
                {'message': 'User created successfully'},
                status=status.HTTP_201_CREATED
            )
        return Response(
            {'message': 'User already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


