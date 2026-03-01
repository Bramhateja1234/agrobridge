"""Crops app models."""
from django.db import models
from django.conf import settings


class Crop(models.Model):
    CROP_TYPE_CHOICES = [
        ('grain', 'Grain'),
        ('vegetable', 'Vegetable'),
        ('fruit', 'Fruit'),
        ('pulse', 'Pulse'),
        ('oilseed', 'Oilseed'),
        ('spice', 'Spice'),
        ('other', 'Other'),
    ]

    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='crops'
    )
    name = models.CharField(max_length=200)
    batch_number = models.CharField(max_length=50, blank=True)
    type = models.CharField(max_length=20, choices=CROP_TYPE_CHOICES, default='other')
    quantity_available = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='crops/', blank=True, null=True)
    description = models.TextField(blank=True)
    out_of_stock = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} by {self.farmer.name}"

    def update_stock(self, quantity_sold):
        """Reduce stock and set out_of_stock if needed."""
        self.quantity_available -= quantity_sold
        if self.quantity_available <= 0:
            self.quantity_available = 0
            self.out_of_stock = True
        self.save()

    def save(self, *args, **kwargs):
        if not self.batch_number:
            import uuid
            self.batch_number = f"BATCH-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)
