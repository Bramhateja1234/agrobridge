"""Orders app models."""
from django.db import models
from django.conf import settings


class OrderStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    CONFIRMED = 'confirmed', 'Confirmed'
    READY_FOR_PICKUP = 'ready_for_pickup', 'Ready for Pickup'
    PICKED_UP = 'picked_up', 'Picked Up'
    OUT_FOR_DELIVERY = 'out_for_delivery', 'Out for Delivery'
    DELIVERED = 'delivered', 'Delivered'
    CANCELLED = 'cancelled', 'Cancelled'


class PaymentStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PAID = 'paid', 'Paid'
    FAILED = 'failed', 'Failed'


# Centralized state machine — reuse in views and serializers
ALLOWED_CANCEL_STATUSES = {
    OrderStatus.PENDING,
    OrderStatus.CONFIRMED,
    OrderStatus.READY_FOR_PICKUP,
}

DELIVERY_FEE = 10  # Platform-retained fee on every cancelled paid order


class Order(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('online', 'Online'),
        ('cod', 'Cash on Delivery'),
    ]
    COD_PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('online', 'Online'),
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
        max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING
    )
    cod_payment_type = models.CharField(
        max_length=10, choices=COD_PAYMENT_CHOICES, blank=True, null=True,
        help_text="How was the COD order eventually paid? (cash or online)"
    )
    order_status = models.CharField(
        max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING
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

    # Refund tracking
    is_cancelled = models.BooleanField(default=False)
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    refund_status = models.CharField(
        max_length=20,
        choices=[('none', 'None'), ('pending', 'Pending'), ('completed', 'Completed')],
        default='none'
    )
    cancelled_by = models.CharField(max_length=20, blank=True, null=True)

    # Idempotency key – one cancel per unique frontend key (double-click / retry safe)
    idempotency_key = models.CharField(max_length=64, blank=True, null=True, db_index=True)

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
                old_status = Order.objects.filter(pk=self.pk).values_list('order_status', flat=True).first()
            except Exception:
                pass

        # Auto-update payment to paid if COD order is delivered
        if self.order_status == OrderStatus.DELIVERED and self.payment_method == 'cod' and self.payment_status != PaymentStatus.PAID:
            self.payment_status = PaymentStatus.PAID

        super().save(*args, **kwargs)

        # Deduct crop stock upon successful delivery
        if not is_new and self.order_status == OrderStatus.DELIVERED and old_status != OrderStatus.DELIVERED:
            if hasattr(self, 'crop') and self.crop:
                self.crop.update_stock(self.quantity)

    def __str__(self):
        return f"Order #{self.id} by {self.consumer.name} – {self.order_status} ({self.payment_status})"


class RefundLog(models.Model):
    """Dedicated audit table for refund events – queryable, never overwritten."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='refund_logs')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=DELIVERY_FEE)
    total_original = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('completed', 'Completed')],
        default='pending'
    )
    cancelled_by = models.CharField(max_length=20, default='consumer')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Refund #{self.id} for Order #{self.order_id} – {self.status}"
