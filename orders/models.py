"""Orders app models."""
from django.db import models
from django.conf import settings


class Order(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('online', 'Online'),
        ('cod', 'Cash on Delivery'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]
    COD_PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('online', 'Online'),
    ]
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('picked_up', 'Picked Up'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    consumer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    crop = models.ForeignKey(
        'crops.Crop',
        on_delete=models.CASCADE,
        related_name='orders'
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(
        max_length=10, choices=PAYMENT_METHOD_CHOICES, default='online'
    )
    payment_status = models.CharField(
        max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending'
    )
    cod_payment_type = models.CharField(
        max_length=10, choices=COD_PAYMENT_CHOICES, blank=True, null=True,
        help_text="How was the COD order eventually paid? (cash or online)"
    )
    order_status = models.CharField(
        max_length=20, choices=ORDER_STATUS_CHOICES, default='pending'
    )
    delivery_address = models.TextField(blank=True, null=True)
    pickup_address = models.TextField(blank=True, null=True)
    
    pickup_qr = models.ImageField(upload_to='qr/pickup/', null=True, blank=True)
    delivery_qr = models.ImageField(upload_to='qr/delivery/', null=True, blank=True)
    
    delivery_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='assigned_deliveries'
    )
    estimated_delivery_time = models.DateTimeField(blank=True, null=True)
    delivery_latitude = models.FloatField(blank=True, null=True)
    delivery_longitude = models.FloatField(blank=True, null=True)
    
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_payment_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None
        if not is_new:
            try:
                # Use values_list to avoid pulling the whole object and prevent extra queries
                old_status = Order.objects.filter(pk=self.pk).values_list('order_status', flat=True).first()
            except Exception:
                pass

        # Auto-update payment to paid if COD order is delivered
        if self.order_status == 'delivered' and self.payment_method == 'cod' and self.payment_status != 'paid':
            self.payment_status = 'paid'
        
        super().save(*args, **kwargs)

        # Deduct crop stock upon successful delivery
        if not is_new and self.order_status == 'delivered' and old_status != 'delivered':
            if hasattr(self, 'crop') and self.crop:
                self.crop.update_stock(self.quantity)

    def __str__(self):
        return f"Order #{self.id} by {self.consumer.name} – {self.order_status} ({self.payment_status})"
