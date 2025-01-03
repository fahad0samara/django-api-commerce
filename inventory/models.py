from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from products.models import Product

class Warehouse(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    contact_person = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class StockLevel(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    reorder_point = models.IntegerField(default=10)
    reorder_quantity = models.IntegerField(default=50)
    last_restock = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('product', 'warehouse')
    
    def __str__(self):
        return f"{self.product} - {self.warehouse} ({self.quantity})"

class InventoryTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('receive', 'Receive'),
        ('ship', 'Ship'),
        ('adjust', 'Adjustment'),
        ('return', 'Return'),
        ('transfer', 'Transfer'),
    )
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()
    reference_number = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        # Update stock level
        stock, created = StockLevel.objects.get_or_create(
            product=self.product,
            warehouse=self.warehouse
        )
        
        if self.transaction_type in ['receive', 'return']:
            stock.quantity += self.quantity
        elif self.transaction_type in ['ship', 'transfer']:
            if stock.quantity < self.quantity:
                raise ValidationError("Insufficient stock")
            stock.quantity -= self.quantity
        else:  # adjust
            stock.quantity = max(0, stock.quantity + self.quantity)
        
        stock.save()
        super().save(*args, **kwargs)

class Supplier(models.Model):
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class PurchaseOrder(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('ordered', 'Ordered'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    )
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    order_date = models.DateTimeField(auto_now_add=True)
    expected_delivery = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"PO-{self.id} ({self.supplier})"

class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    @property
    def total_price(self):
        return self.quantity * self.unit_price
