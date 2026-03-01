"""Payments admin."""
from django.contrib import admin
from .models import PaymentLog


@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'stripe_payment_id', 'amount', 'currency', 'status', 'created_at']
    list_filter = ['status', 'currency']
    search_fields = ['stripe_payment_id', 'order__id']
    ordering = ['-created_at']
