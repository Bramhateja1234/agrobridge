"""Crops admin registration."""
from django.contrib import admin
from .models import Crop


@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'farmer', 'price_per_kg', 'quantity_available', 'out_of_stock', 'created_at']
    list_filter = ['type', 'out_of_stock']
    search_fields = ['name', 'farmer__name', 'farmer__email']
    ordering = ['-created_at']
