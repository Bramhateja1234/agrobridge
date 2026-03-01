"""Reviews views."""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Avg, Count

from .models import Review
from .serializers import ReviewSerializer
from users.permissions import IsConsumer, IsAdminUser
from users.models import CustomUser


class SubmitReviewView(generics.CreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsConsumer]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx


class FarmerReviewsView(APIView):
    """Get all reviews and avg rating for a farmer."""
    permission_classes = []  # Public

    def get(self, request, farmer_id):
        try:
            farmer = CustomUser.objects.get(id=farmer_id, role='farmer')
        except CustomUser.DoesNotExist:
            return Response({'error': 'Farmer not found.'}, status=status.HTTP_404_NOT_FOUND)

        reviews = Review.objects.filter(farmer=farmer, is_moderated=False)
        avg = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        serialized = ReviewSerializer(reviews, many=True).data
        return Response({
            'farmer_name': farmer.name,
            'average_rating': round(avg, 2),
            'total_reviews': reviews.count(),
            'reviews': serialized
        })


class CropReviewsView(generics.ListAPIView):
    """Get all reviews for a specific crop."""
    serializer_class = ReviewSerializer
    permission_classes = []  # Public

    def get_queryset(self):
        crop_id = self.kwargs['crop_id']
        return Review.objects.filter(order__crop_id=crop_id, is_moderated=False)


class AdminModerateReviewView(APIView):
    """Admin: toggle is_moderated on a review."""
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        try:
            review = Review.objects.get(pk=pk)
            review.is_moderated = not review.is_moderated
            review.save()
            return Response({'message': f'Review moderation set to {review.is_moderated}.'})
        except Review.DoesNotExist:
            return Response({'error': 'Review not found.'}, status=status.HTTP_404_NOT_FOUND)


class AdminAllReviewsView(generics.ListAPIView):
    """Admin: all reviews & global stats."""
    serializer_class = ReviewSerializer
    permission_classes = [IsAdminUser]
    queryset = Review.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        avg = queryset.aggregate(avg=Avg('rating'))['avg'] or 0
        stats = {
            'average_rating': round(avg, 2),
            'total_reviews': queryset.count()
        }

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            res = self.get_paginated_response(serializer.data)
            res.data.update(stats)
            return res

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'results': serializer.data,
            **stats
        })
