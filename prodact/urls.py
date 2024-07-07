
from django.urls import path
from . import views


urlpatterns = [
    path("products/",views.get_all_products,name='products' ),
 path("products/<str:pk>/",views.get_by_id_product,name='get_by_id' ),
]