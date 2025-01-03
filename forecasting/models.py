from django.db import models
from django.utils import timezone
from products.models import Product
from inventory.models import Warehouse

class SalesHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    date = models.DateField()
    quantity_sold = models.IntegerField()
    revenue = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        unique_together = ('product', 'warehouse', 'date')
        indexes = [
            models.Index(fields=['product', 'date']),
            models.Index(fields=['warehouse', 'date']),
        ]

class ForecastModel(models.Model):
    ALGORITHM_CHOICES = (
        ('moving_avg', 'Moving Average'),
        ('exp_smoothing', 'Exponential Smoothing'),
        ('arima', 'ARIMA'),
        ('prophet', 'Prophet'),
    )
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    algorithm = models.CharField(max_length=20, choices=ALGORITHM_CHOICES)
    parameters = models.JSONField()  # Store model parameters
    accuracy_metrics = models.JSONField()  # Store accuracy metrics
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('product', 'warehouse', 'algorithm')

class SalesForecast(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    date = models.DateField()
    forecasted_quantity = models.IntegerField()
    confidence_interval_lower = models.IntegerField()
    confidence_interval_upper = models.IntegerField()
    model = models.ForeignKey(ForecastModel, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('product', 'warehouse', 'date', 'model')
        indexes = [
            models.Index(fields=['product', 'date']),
            models.Index(fields=['warehouse', 'date']),
        ]

class SeasonalityPattern(models.Model):
    PATTERN_TYPES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    )
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    pattern_type = models.CharField(max_length=10, choices=PATTERN_TYPES)
    pattern_data = models.JSONField()  # Store seasonality factors
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('product', 'pattern_type')
