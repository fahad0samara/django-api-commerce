from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Avg, StdDev, Q
from django.utils import timezone
from datetime import timedelta
import numpy as np
import logging
from .models import SalesForecast, ForecastModel, SalesHistory

logger = logging.getLogger(__name__)

class ForecastMonitor:
    ALERT_THRESHOLDS = {
        'mape_threshold': 50,  # Alert if MAPE > 50%
        'rmse_threshold': 100,  # Adjust based on your scale
        'anomaly_std_dev': 3,  # Number of standard deviations for anomaly detection
    }
    
    @classmethod
    def check_forecast_accuracy(cls):
        """Monitor forecast accuracy and alert on significant deviations"""
        try:
            # Get recent forecasts
            recent_date = timezone.now().date() - timedelta(days=7)
            forecasts = SalesForecast.objects.filter(
                date__gte=recent_date
            ).select_related('model', 'product', 'warehouse')
            
            alerts = []
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
                    
                    if error > cls.ALERT_THRESHOLDS['mape_threshold']:
                        alerts.append({
                            'product': forecast.product,
                            'warehouse': forecast.warehouse,
                            'error': error,
                            'actual': actual_sales.quantity_sold,
                            'forecast': forecast.forecasted_quantity,
                            'date': forecast.date
                        })
            
            if alerts:
                cls._send_accuracy_alert(alerts)
                
        except Exception as e:
            logger.error(f"Error in forecast monitoring: {str(e)}", exc_info=True)
    
    @classmethod
    def detect_anomalies(cls):
        """Detect anomalies in sales data"""
        try:
            recent_date = timezone.now().date() - timedelta(days=30)
            
            # Get sales statistics
            sales_stats = SalesHistory.objects.filter(
                date__gte=recent_date
            ).values(
                'product', 'warehouse'
            ).annotate(
                avg_sales=Avg('quantity_sold'),
                std_sales=StdDev('quantity_sold')
            )
            
            anomalies = []
            for stat in sales_stats:
                recent_sales = SalesHistory.objects.filter(
                    product_id=stat['product'],
                    warehouse_id=stat['warehouse'],
                    date__gte=timezone.now().date() - timedelta(days=1)
                )
                
                for sale in recent_sales:
                    z_score = abs(
                        sale.quantity_sold - stat['avg_sales']
                    ) / max(1, stat['std_sales'])
                    
                    if z_score > cls.ALERT_THRESHOLDS['anomaly_std_dev']:
                        anomalies.append({
                            'product_id': stat['product'],
                            'warehouse_id': stat['warehouse'],
                            'date': sale.date,
                            'quantity': sale.quantity_sold,
                            'z_score': z_score
                        })
            
            if anomalies:
                cls._send_anomaly_alert(anomalies)
                
        except Exception as e:
            logger.error(f"Error in anomaly detection: {str(e)}", exc_info=True)
    
    @classmethod
    def monitor_model_performance(cls):
        """Monitor and compare different forecasting models"""
        try:
            models = ForecastModel.objects.all()
            performance_data = {}
            
            for model in models:
                metrics = model.accuracy_metrics
                if not metrics:
                    continue
                
                key = f"{model.product_id}_{model.warehouse_id}"
                if key not in performance_data:
                    performance_data[key] = []
                
                performance_data[key].append({
                    'algorithm': model.algorithm,
                    'mape': metrics.get('mape', float('inf')),
                    'rmse': metrics.get('rmse', float('inf')),
                    'model': model
                })
            
            # Find best performing models
            for key, models in performance_data.items():
                if len(models) > 1:
                    # Sort by MAPE (lower is better)
                    models.sort(key=lambda x: x['mape'])
                    best_model = models[0]
                    worst_model = models[-1]
                    
                    # If significant difference in performance
                    if worst_model['mape'] > best_model['mape'] * 1.5:
                        cls._send_model_comparison_alert(best_model, worst_model)
                        
        except Exception as e:
            logger.error(f"Error in model performance monitoring: {str(e)}", exc_info=True)
    
    @staticmethod
    def _send_accuracy_alert(alerts):
        """Send email alert for forecast accuracy issues"""
        try:
            subject = 'Forecast Accuracy Alert'
            message = 'The following forecasts have high error rates:\n\n'
            
            for alert in alerts:
                message += f"""
                Product: {alert['product']}
                Warehouse: {alert['warehouse']}
                Date: {alert['date']}
                Error: {alert['error']:.2f}%
                Actual: {alert['actual']}
                Forecast: {alert['forecast']}
                
                """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=settings.FORECAST_ALERT_EMAILS,
                fail_silently=False
            )
        except Exception as e:
            logger.error(f"Error sending accuracy alert: {str(e)}", exc_info=True)
    
    @staticmethod
    def _send_anomaly_alert(anomalies):
        """Send email alert for sales anomalies"""
        try:
            subject = 'Sales Anomaly Alert'
            message = 'The following sales anomalies were detected:\n\n'
            
            for anomaly in anomalies:
                message += f"""
                Product ID: {anomaly['product_id']}
                Warehouse ID: {anomaly['warehouse_id']}
                Date: {anomaly['date']}
                Quantity: {anomaly['quantity']}
                Z-Score: {anomaly['z_score']:.2f}
                
                """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=settings.FORECAST_ALERT_EMAILS,
                fail_silently=False
            )
        except Exception as e:
            logger.error(f"Error sending anomaly alert: {str(e)}", exc_info=True)
    
    @staticmethod
    def _send_model_comparison_alert(best_model, worst_model):
        """Send email alert for model performance comparison"""
        try:
            subject = 'Forecast Model Performance Alert'
            message = f"""
            Significant difference in model performance detected:
            
            Best Performing Model:
            Algorithm: {best_model['algorithm']}
            MAPE: {best_model['mape']:.2f}%
            RMSE: {best_model['rmse']:.2f}
            
            Worst Performing Model:
            Algorithm: {worst_model['algorithm']}
            MAPE: {worst_model['mape']:.2f}%
            RMSE: {worst_model['rmse']:.2f}
            
            Consider switching to the better performing model.
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=settings.FORECAST_ALERT_EMAILS,
                fail_silently=False
            )
        except Exception as e:
            logger.error(f"Error sending model comparison alert: {str(e)}", exc_info=True)
