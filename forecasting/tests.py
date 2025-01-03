import pytest
from django.utils import timezone
from datetime import timedelta
import numpy as np
from .models import SalesHistory, ForecastModel, SalesForecast
from .services import ForecastingService
from products.models import Product
from inventory.models import Warehouse

@pytest.fixture
def sample_data(db):
    # Create test product and warehouse
    product = Product.objects.create(
        name='Test Product',
        price=100.00
    )
    warehouse = Warehouse.objects.create(
        name='Test Warehouse',
        address='Test Address',
        contact_person='Test Person',
        phone='1234567890',
        email='test@example.com'
    )
    
    # Create historical sales data
    start_date = timezone.now().date() - timedelta(days=90)
    
    # Generate some realistic-looking sales data with trend and seasonality
    for i in range(90):
        date = start_date + timedelta(days=i)
        # Base quantity with upward trend
        base_quantity = 100 + i * 0.5
        # Add weekly seasonality
        weekly_factor = 1 + 0.3 * np.sin(2 * np.pi * (i % 7) / 7)
        # Add some random noise
        noise = np.random.normal(0, 10)
        
        quantity = int(base_quantity * weekly_factor + noise)
        quantity = max(0, quantity)  # Ensure non-negative
        
        SalesHistory.objects.create(
            product=product,
            warehouse=warehouse,
            date=date,
            quantity_sold=quantity,
            revenue=quantity * product.price
        )
    
    return {'product': product, 'warehouse': warehouse}

@pytest.mark.django_db
class TestForecastingService:
    def test_exp_smoothing_forecast(self, sample_data):
        product = sample_data['product']
        warehouse = sample_data['warehouse']
        
        # Generate forecast
        forecasts = ForecastingService.generate_forecast(
            product,
            warehouse,
            days_ahead=30,
            algorithm='exp_smoothing'
        )
        
        assert len(forecasts) == 30
        for forecast in forecasts:
            assert forecast.forecasted_quantity >= 0
            assert forecast.confidence_interval_lower <= forecast.forecasted_quantity
            assert forecast.confidence_interval_upper >= forecast.forecasted_quantity
    
    def test_arima_forecast(self, sample_data):
        product = sample_data['product']
        warehouse = sample_data['warehouse']
        
        forecasts = ForecastingService.generate_forecast(
            product,
            warehouse,
            days_ahead=30,
            algorithm='arima'
        )
        
        assert len(forecasts) == 30
        # Check forecast values are reasonable
        for forecast in forecasts:
            assert 0 <= forecast.forecasted_quantity <= 1000  # Adjust range as needed
    
    def test_seasonality_analysis(self, sample_data):
        product = sample_data['product']
        
        patterns = ForecastingService.analyze_seasonality(product)
        
        assert patterns is not None
        assert 'daily' in patterns
        assert 'monthly' in patterns
        
        # Check daily patterns
        daily_pattern = patterns['daily']
        assert len(daily_pattern) == 7  # 7 days in a week
        
        # Check monthly patterns
        monthly_pattern = patterns['monthly']
        assert len(monthly_pattern) <= 12  # Up to 12 months
    
    def test_forecast_accuracy(self, sample_data):
        product = sample_data['product']
        warehouse = sample_data['warehouse']
        
        # Generate forecast
        ForecastingService.generate_forecast(
            product,
            warehouse,
            days_ahead=30,
            algorithm='exp_smoothing'
        )
        
        # Check accuracy metrics
        model = ForecastModel.objects.get(
            product=product,
            warehouse=warehouse,
            algorithm='exp_smoothing'
        )
        
        assert 'mae' in model.accuracy_metrics
        assert 'rmse' in model.accuracy_metrics
        assert 'mape' in model.accuracy_metrics
        
        # Check metrics are reasonable
        assert 0 <= model.accuracy_metrics['mape'] <= 100
        assert model.accuracy_metrics['mae'] >= 0
        assert model.accuracy_metrics['rmse'] >= 0
    
    def test_no_history_forecast(self, db):
        # Test forecasting with no historical data
        product = Product.objects.create(
            name='New Product',
            price=100.00
        )
        warehouse = Warehouse.objects.create(
            name='New Warehouse',
            address='Address',
            contact_person='Person',
            phone='1234567890',
            email='new@example.com'
        )
        
        forecast = ForecastingService.generate_forecast(
            product,
            warehouse,
            days_ahead=30
        )
        
        assert forecast is None
