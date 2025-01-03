from django.contrib import admin
from .models import (
    SalesHistory,
    ForecastModel,
    SalesForecast,
    SeasonalityPattern
)

@admin.register(SalesHistory)
class SalesHistoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'warehouse', 'date', 'quantity_sold', 'revenue')
    list_filter = ('warehouse', 'date')
    search_fields = ('product__name', 'warehouse__name')
    date_hierarchy = 'date'

@admin.register(ForecastModel)
class ForecastModelAdmin(admin.ModelAdmin):
    list_display = ('product', 'warehouse', 'algorithm', 'last_updated')
    list_filter = ('algorithm', 'last_updated')
    search_fields = ('product__name', 'warehouse__name')

@admin.register(SalesForecast)
class SalesForecastAdmin(admin.ModelAdmin):
    list_display = (
        'product',
        'warehouse',
        'date',
        'forecasted_quantity',
        'created_at'
    )
    list_filter = ('warehouse', 'date', 'created_at')
    search_fields = ('product__name', 'warehouse__name')
    date_hierarchy = 'date'

@admin.register(SeasonalityPattern)
class SeasonalityPatternAdmin(admin.ModelAdmin):
    list_display = ('product', 'pattern_type', 'last_updated')
    list_filter = ('pattern_type', 'last_updated')
    search_fields = ('product__name',)
