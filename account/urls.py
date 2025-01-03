from django.urls import path
from . import views

app_name = 'account'

# Frontend URLs
urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('logout/', views.logout_view, name='logout'),
]

# API URLs
api_urlpatterns = [
    path('register/', views.register, name='api_register'),
    path('userinfo/', views.current_user, name='user_info'),
]

urlpatterns += api_urlpatterns