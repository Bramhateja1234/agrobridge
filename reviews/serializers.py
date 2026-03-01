"""Reviews serializers."""
from rest_framework import serializers
from .models import Review
from django.db.models import Avg


class ReviewSerializer(serializers.ModelSerializer):
    consumer_name = serializers.CharField(source='consumer.name', read_only=True)
    farmer_name = serializers.CharField(source='farmer.name', read_only=True)
    crop_name = serializers.CharField(source='order.crop.name', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'consumer_name', 'farmer_name', 'crop_name', 'order', 'rating', 'comment', 'is_moderated', 'created_at']
        read_only_fields = ['id', 'consumer_name', 'farmer_name', 'crop_name', 'is_moderated', 'created_at']

    def validate(self, attrs):
        request = self.context['request']
        order = attrs.get('order')
        if order.consumer != request.user:
            raise serializers.ValidationError('You can only review your own orders.')
        if order.payment_status != 'paid':
            raise serializers.ValidationError('Can only review after a completed payment.')
        if hasattr(order, 'review'):
            raise serializers.ValidationError('You have already reviewed this order.')
        attrs['consumer'] = request.user
        attrs['farmer'] = order.crop.farmer
        return attrs


class FarmerRatingSerializer(serializers.Serializer):
    farmer_id = serializers.IntegerField()
    farmer_name = serializers.CharField()
    average_rating = serializers.FloatField()
    total_reviews = serializers.IntegerField()
