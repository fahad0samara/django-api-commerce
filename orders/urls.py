from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('create/', views.order_create, name='create'),
    path('list/', views.order_list, name='list'),
    path('detail/<int:order_id>/', views.order_detail, name='detail'),
] 