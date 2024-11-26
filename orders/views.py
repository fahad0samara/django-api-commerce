from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Order, OrderItem
from cart.cart import Cart
from django.core.mail import send_mail
from django.conf import settings
from .utils import generate_pdf_invoice

@login_required
def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        order = Order.objects.create(
            user=request.user,
            shipping_address=request.POST['shipping_address'],
            total_amount=cart.get_total_price()
        )
        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                price=item['price'],
                quantity=item['quantity']
            )
        cart.clear()
        # Send order confirmation email
        send_order_confirmation(order)
        return redirect('orders:order_detail', order.id)
    return render(request, 'orders/create.html')

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