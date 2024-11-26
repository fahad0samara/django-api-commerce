from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Order, OrderItem
from .forms import OrderCreateForm
from cart.cart import Cart
from django.core.mail import send_mail
from django.conf import settings
from .utils import generate_pdf_invoice

@login_required
def order_create(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.error(request, 'Your cart is empty')
        return redirect('cart:detail')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.total_amount = cart.get_total_price()
            order.save()
            
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    price=item['price'],
                    quantity=item['quantity']
                )
            
            # Clear the cart
            cart.clear()
            
            # Send confirmation email
            order.send_confirmation_email()
            
            messages.success(request, 'Order placed successfully')
            return redirect('orders:detail', order_id=order.id)
    else:
        form = OrderCreateForm()
    
    return render(request, 'orders/create.html', {
        'cart': cart,
        'form': form
    })

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created')
    return render(request, 'orders/list.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/detail.html', {'order': order})

@login_required
def order_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return generate_pdf_invoice(order)

def send_order_confirmation(order):
    subject = f'Order #{order.id} Confirmation'
    message = f'''
    Thank you for your order!
    Order ID: {order.id}
    Total Amount: ${order.total_amount}
    Status: {order.status}
    
    We will process your order soon.
    '''
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [order.user.email],
        fail_silently=False,
    ) 