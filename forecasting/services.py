import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Sum
from django.core.cache import cache
from django.conf import settings
import logging

from .models import SalesHistory, ForecastModel, SalesForecast, SeasonalityPattern

logger = logging.getLogger(__name__)

class ForecastingService:
    CACHE_TTL = 3600  # 1 hour cache
    MIN_HISTORY_DAYS = 30  # Minimum days of history needed
    
    @classmethod
    def generate_forecast(cls, product, warehouse, days_ahead=30, algorithm='exp_smoothing'):
        """Generate sales forecast for a product"""
        cache_key = f'forecast_{product.id}_{warehouse.id}_{algorithm}'
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # Get historical data
            history = SalesHistory.objects.filter(
                product=product,
                warehouse=warehouse
            ).order_by('date')
            
            if not history.exists() or history.count() < cls.MIN_HISTORY_DAYS:
                logger.warning(f"Insufficient history for product {product.id}")
                return None
            
            # Convert to time series
            ts_data = pd.DataFrame(
                list(history.values('date', 'quantity_sold')),
            ).set_index('date')
            
            # Handle missing dates
            date_range = pd.date_range(
                start=ts_data.index.min(),
                end=ts_data.index.max()
            )
            ts_data = ts_data.reindex(date_range, fill_value=0)
            
            # Get or create forecast model
            model, _ = ForecastModel.objects.get_or_create(
                product=product,
                warehouse=warehouse,
                algorithm=algorithm,
                defaults={'parameters': {}, 'accuracy_metrics': {}}
            )
            
            # Generate forecast based on algorithm
            forecast_method = getattr(cls, f'_{algorithm}_forecast')
            forecasted_values = forecast_method(ts_data, days_ahead)
            
            if not forecasted_values:
                logger.error(f"Failed to generate forecast for product {product.id}")
                return None
            
            # Save forecasts
            forecasts = []
            start_date = timezone.now().date()
            
            for i, (forecast, lower, upper) in enumerate(forecasted_values):
                forecast_date = start_date + timedelta(days=i)
                forecasts.append(
                    SalesForecast(
                        product=product,
                        warehouse=warehouse,
                        date=forecast_date,
                        forecasted_quantity=max(0, int(forecast)),  # Ensure non-negative
                        confidence_interval_lower=max(0, int(lower)),
                        confidence_interval_upper=max(0, int(upper)),
                        model=model
                    )
                )
            
            # Bulk create forecasts
            SalesForecast.objects.bulk_create(forecasts)
            
            # Update model metrics
            model.accuracy_metrics = cls._calculate_accuracy_metrics(
                ts_data, forecasted_values[:len(ts_data)]
            )
            model.save()
            
            # Cache the results
            cache.set(cache_key, forecasts, cls.CACHE_TTL)
            
            return forecasts
            
        except Exception as e:
            logger.error(f"Error generating forecast: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def _exp_smoothing_forecast(data, days_ahead):
        """Generate forecast using Exponential Smoothing"""
        try:
            if len(data) < 2:
                return None
                
            model = ExponentialSmoothing(
                data['quantity_sold'],
                seasonal_periods=7,  # Weekly seasonality
                trend='add',
                seasonal='add',
                initialization_method='estimated'
            )
            fitted_model = model.fit(optimized=True)
            
            forecast = fitted_model.forecast(days_ahead)
            confidence_intervals = fitted_model.get_prediction(
                start=len(data),
                end=len(data) + days_ahead - 1
            ).conf_int()
            
            return list(zip(
                forecast,
                confidence_intervals[:, 0],
                confidence_intervals[:, 1]
            ))
        except Exception as e:
            logger.error(f"Error in exp_smoothing_forecast: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def _arima_forecast(data, days_ahead):
        """Generate forecast using ARIMA"""
        try:
            if len(data) < 2:
                return None
                
            model = ARIMA(
                data['quantity_sold'],
                order=(1, 1, 1),
                enforce_stationarity=False
            )
            fitted_model = model.fit()
            
            forecast = fitted_model.forecast(days_ahead)
            confidence_intervals = fitted_model.get_forecast(
                days_ahead
            ).conf_int()
            
            return list(zip(
                forecast,
                confidence_intervals[:, 0],
                confidence_intervals[:, 1]
            ))
        except Exception as e:
            logger.error(f"Error in arima_forecast: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def _prophet_forecast(data, days_ahead):
        """Generate forecast using Prophet"""
        try:
            if len(data) < 2:
                return None
                
            # Prepare data for Prophet
            df = data.reset_index()
            df.columns = ['ds', 'y']
            
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                interval_width=0.95
            )
            model.fit(df)
            
            future_dates = model.make_future_dataframe(periods=days_ahead)
            forecast = model.predict(future_dates)
            
            return list(zip(
                forecast['yhat'].tail(days_ahead),
                forecast['yhat_lower'].tail(days_ahead),
                forecast['yhat_upper'].tail(days_ahead)
            ))
        except Exception as e:
            logger.error(f"Error in prophet_forecast: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def _calculate_accuracy_metrics(actual_data, forecasted_values):
        """Calculate forecast accuracy metrics"""
        try:
            actual = actual_data['quantity_sold'].values
            predicted = np.array([f[0] for f in forecasted_values])
            
            # Handle division by zero in MAPE calculation
            mape = np.mean(np.abs((actual - predicted) / np.where(actual == 0, 1, actual))) * 100
            
            return {
                'mae': float(mean_absolute_error(actual, predicted)),
                'rmse': float(np.sqrt(mean_squared_error(actual, predicted))),
                'mape': float(mape)
            }
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}", exc_info=True)
            return {'mae': 0, 'rmse': 0, 'mape': 0}
    
    @staticmethod
    def _moving_average_forecast(data, days_ahead):
        """Generate forecast using Moving Average"""
        window_size = 7  # 7-day moving average
        ma = data['quantity_sold'].rolling(window=window_size).mean()
        
        # Use the last MA value for all future predictions
        last_ma = ma.iloc[-1]
        std = data['quantity_sold'].std()
        
        forecasts = [(last_ma, last_ma - 2*std, last_ma + 2*std) for _ in range(days_ahead)]
        return forecasts
    
    @staticmethod
    def analyze_seasonality(product):
        """Analyze and store seasonality patterns"""
        history = SalesHistory.objects.filter(product=product)
        
        if not history.exists():
            return None
        
        # Daily pattern
        daily_pattern = history.values('date__weekday').annotate(
            avg_sales=Avg('quantity_sold')
        ).order_by('date__weekday')
        
        # Monthly pattern
        monthly_pattern = history.values('date__month').annotate(
            avg_sales=Avg('quantity_sold')
        ).order_by('date__month')
        
        # Store patterns
        SeasonalityPattern.objects.update_or_create(
            product=product,
            pattern_type='daily',
            defaults={'pattern_data': list(daily_pattern)}
        )
        
        SeasonalityPattern.objects.update_or_create(
            product=product,
            pattern_type='monthly',
            defaults={'pattern_data': list(monthly_pattern)}
        )
        
        return {
            'daily': daily_pattern,
            'monthly': monthly_pattern
        }
