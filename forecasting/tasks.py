from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from products.models import Product
from inventory.models import Warehouse
from .services import ForecastingService

@shared_task
def update_all_forecasts():
    """Update forecasts for all products"""
    # Get products with sufficient sales history
    products = Product.objects.annotate(
        history_count=Count('saleshistory')
    ).filter(history_count__gte=30)  # At least 30 days of history
    
    warehouses = Warehouse.objects.filter(is_active=True)
    
    for product in products:
        for warehouse in warehouses:
            update_product_forecast.delay(product.id, warehouse.id)

@shared_task
def update_product_forecast(product_id, warehouse_id):
    """Update forecast for a specific product"""
    try:
        product = Product.objects.get(id=product_id)
        warehouse = Warehouse.objects.get(id=warehouse_id)
        
        # Generate forecasts using different algorithms
        algorithms = ['exp_smoothing', 'arima', 'prophet']
        best_forecast = None
        best_accuracy = float('inf')
        
        for algorithm in algorithms:
            forecast = ForecastingService.generate_forecast(
                product,
                warehouse,
                days_ahead=30,
                algorithm=algorithm
            )
            
            if forecast:
                model = forecast[0].model
                accuracy = model.accuracy_metrics.get('mape', float('inf'))
                
                if accuracy < best_accuracy:
                    best_accuracy = accuracy
                    best_forecast = forecast
        
        if best_forecast:
            # Update inventory reorder points based on forecast
            update_reorder_points.delay(product.id, warehouse.id)
            
    except (Product.DoesNotExist, Warehouse.DoesNotExist):
        pass

@shared_task
def analyze_seasonality_patterns():
    """Analyze seasonality patterns for all products"""
    products = Product.objects.all()
    
    for product in products:
        ForecastingService.analyze_seasonality(product)

@shared_task
def update_reorder_points(product_id, warehouse_id):
    """Update reorder points based on forecasts"""
    from inventory.models import StockLevel
    
    try:
        product = Product.objects.get(id=product_id)
        warehouse = Warehouse.objects.get(id=warehouse_id)
        
        # Get the latest forecast
        latest_forecast = SalesForecast.objects.filter(
            product=product,
            warehouse=warehouse,
            date__gte=timezone.now().date()
        ).order_by('date')[:7]  # Next 7 days
        
        if latest_forecast:
            # Calculate new reorder point based on forecast
            max_daily_forecast = max(f.forecasted_quantity for f in latest_forecast)
            safety_stock = max_daily_forecast * 2  # 2 days of safety stock
            
            stock_level, _ = StockLevel.objects.get_or_create(
                product=product,
                warehouse=warehouse
            )
            
            stock_level.reorder_point = safety_stock
            stock_level.reorder_quantity = max_daily_forecast * 7  # 1 week supply
            stock_level.save()
            
    except (Product.DoesNotExist, Warehouse.DoesNotExist):
        pass

@shared_task
def cleanup_old_forecasts():
    """Clean up old forecasts to prevent database bloat"""
    cutoff_date = timezone.now().date() - timedelta(days=90)
    SalesForecast.objects.filter(date__lt=cutoff_date).delete()
