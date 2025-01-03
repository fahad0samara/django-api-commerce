from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from .models import Product, Category

def product_list(request):
    category_slug = request.GET.get('category')
    sort = request.GET.get('sort', 'name')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    search = request.GET.get('q')

    products = Product.objects.filter(available=True)
    categories = Category.objects.all()

    # Category filter
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    # Price filter
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # Search filter
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(category__name__icontains=search)
        )

    # Sorting
    if sort == '-price':
        products = products.order_by('-price')
    elif sort == 'price':
        products = products.order_by('price')
    elif sort == '-created':
        products = products.order_by('-created')
    else:
        products = products.order_by('name')

    # Pagination
    paginator = Paginator(products, 12)  # 12 products per page
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    context = {
        'products': products,
        'categories': categories,
        'current_category': category_slug,
        'current_sort': sort
    }
    return render(request, 'products/list.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'products/detail.html', context) 