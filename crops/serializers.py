"""Crops app serializers."""
from rest_framework import serializers
from .models import Crop
from users.serializers import UserProfileSerializer


class CropSerializer(serializers.ModelSerializer):
    farmer_name = serializers.CharField(source='farmer.name', read_only=True)
    farmer_id = serializers.IntegerField(source='farmer.id', read_only=True)
    farmer_latitude = serializers.DecimalField(
        source='farmer.latitude', max_digits=9, decimal_places=6, read_only=True
    )
    farmer_longitude = serializers.DecimalField(
        source='farmer.longitude', max_digits=9, decimal_places=6, read_only=True
    )
    image_url = serializers.SerializerMethodField()
    total_orders = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Crop
        fields = [
            'id', 'farmer_id', 'farmer_name', 'farmer_latitude', 'farmer_longitude',
            'name', 'batch_number', 'type', 'quantity_available', 'price_per_kg',
            'image', 'image_url', 'description', 'out_of_stock', 'created_at', 'updated_at',
            'total_orders', 'average_rating'
        ]
        read_only_fields = ['id', 'batch_number', 'out_of_stock', 'created_at', 'updated_at',
                            'farmer_name', 'farmer_id', 'farmer_latitude', 'farmer_longitude']

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None

    def get_total_orders(self, obj):
        from orders.models import Order
        return Order.objects.filter(crop=obj, payment_status='paid').count()

    def get_average_rating(self, obj):
        from reviews.models import Review
        from django.db.models import Avg
        avg = Review.objects.filter(order__crop=obj, is_moderated=False).aggregate(avg=Avg('rating'))['avg']
        return round(avg, 2) if avg else 0.0

    def validate_quantity_available(self, value):
        if value < 0:
            raise serializers.ValidationError('Quantity cannot be negative.')
        return value

    def validate_price_per_kg(self, value):
        if value <= 0:
            raise serializers.ValidationError('Price must be positive.')
        return value
