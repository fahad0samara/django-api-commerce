import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from orders.models import Order
from .models import Payment

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    if event.type == 'checkout.session.completed':
        session = event.data.object
        order_id = session.metadata.order_id
        order = Order.objects.get(id=order_id)
        Payment.objects.create(
            order=order,
            stripe_id=session.payment_intent,
            amount=session.amount_total / 100,
            status='completed'
        )
        order.paid = True
        order.save()

    return HttpResponse(status=200) 