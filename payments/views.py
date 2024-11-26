import stripe
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from orders.models import Order
from .models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
def payment_process(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        success_url = request.build_absolute_uri(f'/payment/success/{order.id}/')
        cancel_url = request.build_absolute_uri(f'/payment/cancel/{order.id}/')

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int(order.total_amount * 100),
                    'product_data': {
                        'name': f'Order #{order.id}'
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return redirect(session.url)
    
    return render(request, 'payments/process.html', {'order': order})

def payment_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.paid = True
    order.save()
    return render(request, 'payments/success.html')

def payment_cancel(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'payments/cancel.html') 