"""Payments serializers."""
from rest_framework import serializers
from .models import PaymentLog


class PaymentLogSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    consumer_name = serializers.CharField(source='order.consumer.name', read_only=True)
    crop_name = serializers.CharField(source='order.crop.name', read_only=True)

    class Meta:
        model = PaymentLog
        fields = [
            'id', 'order_id', 'consumer_name', 'crop_name',
            'stripe_payment_id', 'stripe_session_id',
            'amount', 'currency', 'status', 'created_at'
        ]
        read_only_fields = fields
