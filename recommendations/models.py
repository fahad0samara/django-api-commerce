from django.db import models
from django.conf import settings
from products.models import Product

class UserProductInteraction(models.Model):
    INTERACTION_TYPES = (
        ('view', 'View'),
        ('cart_add', 'Added to Cart'),
        ('purchase', 'Purchase'),
        ('wishlist', 'Added to Wishlist'),
        ('review', 'Review'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    weight = models.FloatField(default=1.0)  # Different interactions have different weights
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'product', 'interaction_type']),
        ]

class ProductSimilarity(models.Model):
    product_a = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='similarities_as_a')
    product_b = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='similarities_as_b')
    similarity_score = models.FloatField()
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('product_a', 'product_b')
        indexes = [
            models.Index(fields=['product_a', 'similarity_score']),
            models.Index(fields=['product_b', 'similarity_score']),
        ]

class UserPreferences(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    favorite_categories = models.ManyToManyField('products.Category')
    price_range_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_range_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preferred_brands = models.ManyToManyField('products.Brand')
    last_updated = models.DateTimeField(auto_now=True)
