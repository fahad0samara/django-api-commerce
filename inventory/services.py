from django.db.models import F, Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction

from .models import (
    StockLevel, InventoryTransaction, PurchaseOrder,
    PurchaseOrderItem, Warehouse, Supplier
)

class InventoryService:
    @staticmethod
    def check_stock_levels():
        """Check for products that need reordering"""
        low_stock = StockLevel.objects.filter(
            quantity__lte=F('reorder_point')
        ).select_related('product', 'warehouse')
        
        for stock in low_stock:
            InventoryService.create_purchase_order(
                stock.product,
                stock.warehouse,
                stock.reorder_quantity
            )
    
    @staticmethod
    def create_purchase_order(product, warehouse, quantity):
        """Create a purchase order for a product"""
        # Find the best supplier based on history
        supplier = InventoryService._get_best_supplier(product)
        
        if not supplier:
            return None
        
        with transaction.atomic():
            po = PurchaseOrder.objects.create(
                supplier=supplier,
                warehouse=warehouse,
                status='draft',
                expected_delivery=timezone.now().date() + timedelta(days=7),
                total_amount=quantity * product.price  # Use last known price
            )
            
            PurchaseOrderItem.objects.create(
                purchase_order=po,
                product=product,
                quantity=quantity,
                unit_price=product.price
            )
            
            # Send notification
            InventoryService._notify_low_stock(product, warehouse, quantity)
        
        return po
    
    @staticmethod
    def process_stock_transfer(from_warehouse, to_warehouse, product, quantity):
        """Transfer stock between warehouses"""
        with transaction.atomic():
            # Create outbound transaction
            InventoryTransaction.objects.create(
                product=product,
                warehouse=from_warehouse,
                transaction_type='transfer',
                quantity=quantity,
                reference_number=f'TRF-{timezone.now().strftime("%Y%m%d%H%M%S")}',
                notes=f'Transfer to {to_warehouse.name}'
            )
            
            # Create inbound transaction
            InventoryTransaction.objects.create(
                product=product,
                warehouse=to_warehouse,
                transaction_type='receive',
                quantity=quantity,
                reference_number=f'TRF-{timezone.now().strftime("%Y%m%d%H%M%S")}',
                notes=f'Transfer from {from_warehouse.name}'
            )
    
    @staticmethod
    def get_inventory_report(start_date=None, end_date=None, warehouse=None):
        """Generate inventory report"""
        queryset = InventoryTransaction.objects.all()
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        if warehouse:
            queryset = queryset.filter(warehouse=warehouse)
        
        report = {
            'transactions': queryset.count(),
            'total_received': queryset.filter(
                transaction_type='receive'
            ).aggregate(total=Sum('quantity'))['total'] or 0,
            'total_shipped': queryset.filter(
                transaction_type='ship'
            ).aggregate(total=Sum('quantity'))['total'] or 0,
            'low_stock_items': StockLevel.objects.filter(
                quantity__lte=F('reorder_point')
            ).count(),
            'warehouse_summary': StockLevel.objects.values(
                'warehouse__name'
            ).annotate(
                total_items=Count('product'),
                total_quantity=Sum('quantity')
            )
        }
        
        return report
    
    @staticmethod
    def _get_best_supplier(product):
        """Get the best supplier based on history"""
        return Supplier.objects.filter(
            is_active=True
        ).annotate(
            total_orders=Count('purchaseorder'),
            avg_delivery_days=Avg(
                ExpressionWrapper(
                    F('purchaseorder__order_date') - F('purchaseorder__expected_delivery'),
                    output_field=DurationField()
                )
            )
        ).order_by('-total_orders', 'avg_delivery_days').first()
    
    @staticmethod
    def _notify_low_stock(product, warehouse, quantity):
        """Send notification for low stock"""
        subject = f'Low Stock Alert: {product.name}'
        message = f"""
        Low stock alert for {product.name} at {warehouse.name}
        Current quantity: {quantity}
        Reorder point: {StockLevel.objects.get(product=product, warehouse=warehouse).reorder_point}
        
        A purchase order has been automatically created.
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[warehouse.email],
            fail_silently=False,
        )
