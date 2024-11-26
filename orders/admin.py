from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'paid', 'created', 'total_amount', 'order_actions']
    list_filter = ['status', 'paid', 'created', 'updated']
    inlines = [OrderItemInline]
    search_fields = ['user__username', 'shipping_address']
    
    def order_actions(self, obj):
        return format_html(
            '<a class="button" href="{}">Invoice</a>&nbsp;'
            '<a class="button" href="{}">Track</a>',
            reverse('admin:order_invoice', args=[obj.pk]),
            reverse('admin:order_tracking', args=[obj.pk])
        )
    
    order_actions.short_description = 'Actions'
 