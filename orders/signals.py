"""Orders signals – reduce crop stock after successful payment."""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import Order


@receiver(post_save, sender=Order)
def update_crop_stock(sender, instance, **kwargs):
    """When order is marked as paid, reduce crop quantity atomically."""
    if instance.payment_status == 'paid':
        with transaction.atomic():
            crop = instance.crop
            crop.refresh_from_db()
            crop.quantity_available = max(0, crop.quantity_available - instance.quantity)
            if crop.quantity_available == 0:
                crop.out_of_stock = True
            crop.save()
