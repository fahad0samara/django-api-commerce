from django.db import models
from django.conf import settings

# Create your models here.
class Category(models.TextChoices):
    ELECTRONIC='EL','Electronic'
    FASHION='FA','Fashion'
    BOOK='BO','Book'
    SPORT='SP','Sport'
    HOME='HO','Home'
    OTHER='OT','Other'


class Product(models.Model):
    name=models.CharField(max_length=100)
    description=models.TextField()
    price=models.DecimalField(max_digits=10,decimal_places=2)
    category=models.CharField(max_length=40,choices=Category.choices)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
    

    


 
    