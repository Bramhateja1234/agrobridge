"""Orders admin."""
from django.contrib import admin
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'consumer', 'crop', 'quantity', 'total_price', 'payment_status', 'created_at']
    list_filter = ['payment_status']
    search_fields = ['consumer__name', 'consumer__email', 'crop__name']
    ordering = ['-created_at']
