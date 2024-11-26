from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib import messages
from products.models import Product, Category

def home(request):
    featured_products = Product.objects.filter(available=True)[:6]
    categories = Category.objects.all()
    return render(request, 'home.html', {
        'featured_products': featured_products,
        'categories': categories
    })

def about(request):
    return render(request, 'about.html')

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Send email
        email_message = f"From: {name}\nEmail: {email}\n\n{message}"
        try:
            send_mail(
                subject,
                email_message,
                email,
                ['support@emarket.com'],
                fail_silently=False,
            )
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('contact')
        except:
            messages.error(request, 'There was an error sending your message. Please try again later.')
    
    return render(request, 'contact.html') 