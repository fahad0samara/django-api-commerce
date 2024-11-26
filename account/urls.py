from django.urls import path
from . import views

urlpatterns = [
    path('', views.api_root, name='api-root'),
    path('register/', views.register, name='register'),
    path('userinfo/', views.current_user, name='user_info'),
]