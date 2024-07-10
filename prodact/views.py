from django.shortcuts import get_object_or_404, render
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .filters import ProductFilter
from .models import Product
from .serializers import ProductSerializer

# Create your views here.

@api_view(['GET'])
def get_all_products(request):
    filterSet = ProductFilter(request.GET,queryset=Product.objects.all().order_by('id'))
    serializers = ProductSerializer(filterSet.qs,many=True)
    return Response({"products":serializers.data})

@api_view(['GET'])
def get_by_id_product(request,pk):
    product = get_object_or_404(Product,id=pk)
    serializers =ProductSerializer(product,many=False)
    return Response(serializers.data)
