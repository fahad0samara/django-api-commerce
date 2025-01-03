from django.apps import AppConfig

class ForecastingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'forecasting'
    
    def ready(self):
        try:
            import forecasting.signals
        except ImportError:
            pass
