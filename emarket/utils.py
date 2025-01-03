import uuid
from django.utils.text import slugify
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def generate_unique_slug(model_instance, slugable_field_name, slug_field_name):
    """
    Generate unique slug for a model instance
    """
    slug = slugify(getattr(model_instance, slugable_field_name))
    unique_slug = slug
    extension = 1
    ModelClass = model_instance.__class__

    while ModelClass._default_manager.filter(
        **{slug_field_name: unique_slug}
    ).exists():
        unique_slug = f'{slug}-{extension}'
        extension += 1

    return unique_slug

def generate_unique_code(length=8):
    """
    Generate unique code for order number, tracking number etc.
    """
    return str(uuid.uuid4()).split('-')[0][:length].upper()

def send_email_template(subject, template_name, context, recipient_list):
    """
    Send email using HTML template
    """
    html_message = render_to_string(template_name, context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        html_message=html_message,
        fail_silently=False,
    )

def get_client_ip(request):
    """
    Get client IP address from request
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def format_currency(amount, currency='USD'):
    """
    Format currency amount
    """
    if currency == 'USD':
        return f'${amount:,.2f}'
    return f'{amount:,.2f} {currency}'
