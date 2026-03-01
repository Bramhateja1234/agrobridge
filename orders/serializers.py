"""Orders serializers."""
from rest_framework import serializers
from .models import Order
from crops.serializers import CropSerializer


class OrderSerializer(serializers.ModelSerializer):
    crop_name = serializers.CharField(source='crop.name', read_only=True)
    crop_price = serializers.DecimalField(source='crop.price_per_kg', max_digits=10, decimal_places=2, read_only=True)
    consumer_name = serializers.CharField(source='consumer.name', read_only=True)
    farmer_name = serializers.CharField(source='crop.farmer.name', read_only=True)
    consumer_id = serializers.IntegerField(source='consumer.id', read_only=True)
    farmer_id = serializers.IntegerField(source='crop.farmer.id', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'consumer_name', 'farmer_name', 'consumer_id', 'farmer_id', 'crop', 'crop_name', 'crop_price',
            'quantity', 'total_price', 'payment_method', 'payment_status', 'cod_payment_type', 'order_status',
            'pickup_address', 'delivery_address', 'estimated_delivery_time', 'delivery_latitude', 'delivery_longitude',
            'delivery_agent', 'pickup_qr', 'delivery_qr', 'stripe_session_id', 'stripe_payment_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_price', 'payment_status', 'order_status',
                            'estimated_delivery_time', 'stripe_session_id', 'stripe_payment_id', 'created_at', 'updated_at']


class PlaceOrderSerializer(serializers.Serializer):
    crop_id = serializers.IntegerField()
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method = serializers.ChoiceField(choices=['online', 'cod'], default='online')
    delivery_address = serializers.CharField(required=False, allow_blank=True)
    delivery_latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    delivery_longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)

    def validate(self, attrs):
        from crops.models import Crop
        try:
            crop = Crop.objects.get(id=attrs['crop_id'])
        except Crop.DoesNotExist:
            raise serializers.ValidationError({'crop_id': 'Crop not found.'})
        if crop.out_of_stock:
            raise serializers.ValidationError({'crop_id': 'This crop is out of stock.'})
        if attrs['quantity'] > crop.quantity_available:
            raise serializers.ValidationError(
                {'quantity': f'Only {crop.quantity_available}kg available.'}
            )
        attrs['crop'] = crop
        base_price = round(float(crop.price_per_kg) * float(attrs['quantity']), 2)
        attrs['total_price'] = base_price + 30 if base_price < 50 else base_price
        return attrs
