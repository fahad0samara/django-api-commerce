from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
import pandas as pd

from products.models import Product
from inventory.models import Warehouse
from .models import SalesHistory, SalesForecast
from .services import ForecastingService
from .monitoring import ForecastMonitor
from .data_validation import DataValidator
from .model_selection import ModelSelector

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_forecast(request, product_id, warehouse_id):
    """Generate forecast for a product in a warehouse"""
    try:
        product = get_object_or_404(Product, id=product_id)
        warehouse = get_object_or_404(Warehouse, id=warehouse_id)
        
        # Get historical data
        history = SalesHistory.objects.filter(
            product=product,
            warehouse=warehouse
        ).order_by('date')
        
        if not history.exists():
            return Response(
                {"error": "No historical data available"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Convert to DataFrame
        data = pd.DataFrame(
            list(history.values('date', 'quantity_sold'))
        ).set_index('date')
        
        # Validate and clean data
        validator = DataValidator(data)
        if not validator.validate_data():
            return Response(
                {"error": "Data validation failed"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cleaned_data = validator.clean_data()
        
        # Select best model
        selector = ModelSelector(cleaned_data)
        best_model = selector.select_best_model()
        
        if not best_model:
            return Response(
                {"error": "Model selection failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Generate forecast
        forecasts = ForecastingService.generate_forecast(
            product,
            warehouse,
            algorithm=best_model['algorithm']
        )
        
        if not forecasts:
            return Response(
                {"error": "Forecast generation failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Format response
        forecast_data = [{
            'date': forecast.date,
            'quantity': forecast.forecasted_quantity,
            'lower_bound': forecast.confidence_interval_lower,
            'upper_bound': forecast.confidence_interval_upper
        } for forecast in forecasts]
        
        return Response({
            'product': product.name,
            'warehouse': warehouse.name,
            'algorithm': best_model['algorithm'],
            'metrics': best_model['metrics'],
            'forecasts': forecast_data
        })
        
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def monitor_forecasts(request):
    """Get forecast monitoring summary"""
    try:
        # Check forecast accuracy
        ForecastMonitor.check_forecast_accuracy()
        
        # Get recent forecasts
        recent_date = timezone.now().date() - timedelta(days=7)
        forecasts = SalesForecast.objects.filter(
            date__gte=recent_date
        ).select_related('model', 'product', 'warehouse')
        
        # Format response
        monitoring_data = []
        for forecast in forecasts:
            actual_sales = SalesHistory.objects.filter(
                product=forecast.product,
                warehouse=forecast.warehouse,
                date=forecast.date
            ).first()
            
            if actual_sales:
                error = abs(
                    actual_sales.quantity_sold - forecast.forecasted_quantity
                ) / max(1, actual_sales.quantity_sold) * 100
                
                monitoring_data.append({
                    'product': forecast.product.name,
                    'warehouse': forecast.warehouse.name,
                    'date': forecast.date,
                    'forecasted': forecast.forecasted_quantity,
                    'actual': actual_sales.quantity_sold,
                    'error_percentage': error
                })
        
        return Response(monitoring_data)
        
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def forecast_accuracy(request):
    """Get forecast accuracy metrics"""
    try:
        models = ForecastModel.objects.all()
        accuracy_data = []
        
        for model in models:
            if model.accuracy_metrics:
                accuracy_data.append({
                    'product': model.product.name,
                    'warehouse': model.warehouse.name,
                    'algorithm': model.algorithm,
                    'metrics': model.accuracy_metrics
                })
        
        return Response(accuracy_data)
        
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def detect_anomalies(request):
    """Detect sales anomalies"""
    try:
        ForecastMonitor.detect_anomalies()
        recent_date = timezone.now().date() - timedelta(days=30)
        
        # Get sales statistics
        sales_stats = SalesHistory.objects.filter(
            date__gte=recent_date
        ).values(
            'product__name',
            'warehouse__name'
        ).annotate(
            avg_sales=Avg('quantity_sold'),
            std_sales=StdDev('quantity_sold')
        )
        
        anomalies = []
        for stat in sales_stats:
            recent_sales = SalesHistory.objects.filter(
                product__name=stat['product__name'],
                warehouse__name=stat['warehouse__name'],
                date__gte=timezone.now().date() - timedelta(days=1)
            )
            
            for sale in recent_sales:
                z_score = abs(
                    sale.quantity_sold - stat['avg_sales']
                ) / max(1, stat['std_sales'])
                
                if z_score > 3:  # More than 3 standard deviations
                    anomalies.append({
                        'product': stat['product__name'],
                        'warehouse': stat['warehouse__name'],
                        'date': sale.date,
                        'quantity': sale.quantity_sold,
                        'z_score': z_score
                    })
        
        return Response(anomalies)
        
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
