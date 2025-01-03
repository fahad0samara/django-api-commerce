from django.urls import path
from . import views

app_name = 'forecasting'

urlpatterns = [
    path(
        'forecast/<int:product_id>/<int:warehouse_id>/',
        views.generate_forecast,
        name='generate_forecast'
    ),
    path(
        'forecast/monitor/',
        views.monitor_forecasts,
        name='monitor_forecasts'
    ),
    path(
        'forecast/accuracy/',
        views.forecast_accuracy,
        name='forecast_accuracy'
    ),
    path(
        'forecast/anomalies/',
        views.detect_anomalies,
        name='detect_anomalies'
    ),
]
