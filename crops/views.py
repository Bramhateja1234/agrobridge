"""Crops app views with Haversine location filter."""
import math
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import Crop
from .serializers import CropSerializer
from users.permissions import IsFarmer


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in km using Haversine formula."""
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


class CropListView(generics.ListAPIView):
    """List all available crops with filters."""
    serializer_class = CropSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Crop.objects.filter(out_of_stock=False).select_related('farmer')

        # Filter by type
        crop_type = self.request.query_params.get('type')
        if crop_type:
            queryset = queryset.filter(type=crop_type)

        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price_per_kg__gte=min_price)
        if max_price:
            queryset = queryset.filter(price_per_kg__lte=max_price)

        # Filter by location
        lat = self.request.query_params.get('lat')
        lon = self.request.query_params.get('lon')
        radius = self.request.query_params.get('radius', 10)

        if lat and lon:
            try:
                lat, lon, radius = float(lat), float(lon), float(radius)
                nearby_ids = []
                for crop in queryset:
                    if crop.farmer.latitude and crop.farmer.longitude:
                        dist = haversine_distance(lat, lon, crop.farmer.latitude, crop.farmer.longitude)
                        if dist <= radius:
                            nearby_ids.append(crop.id)
                queryset = queryset.filter(id__in=nearby_ids)
            except (ValueError, TypeError):
                pass

        return queryset


class CropDetailView(generics.RetrieveAPIView):
    serializer_class = CropSerializer
    permission_classes = [AllowAny]
    queryset = Crop.objects.all()


class CropCreateView(generics.CreateAPIView):
    serializer_class = CropSerializer
    permission_classes = [IsFarmer]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def perform_create(self, serializer):
        if not self.request.user.is_verified:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Your account must be manually verified by an Admin before you can add crops.")
        serializer.save(farmer=self.request.user)


class CropUpdateView(generics.UpdateAPIView):
    serializer_class = CropSerializer
    permission_classes = [IsFarmer]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return Crop.objects.filter(farmer=self.request.user)


class CropDeleteView(generics.DestroyAPIView):
    permission_classes = [IsFarmer]

    def get_queryset(self):
        return Crop.objects.filter(farmer=self.request.user)


class FarmerCropListView(generics.ListAPIView):
    """Farmer's own crops."""
    serializer_class = CropSerializer
    permission_classes = [IsFarmer]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin' or user.is_superuser:
            return Crop.objects.all().select_related('farmer')
        return Crop.objects.filter(farmer=user)


class AllCropsAdminView(generics.ListAPIView):
    """Admin: all crops."""
    serializer_class = CropSerializer

    def get_queryset(self):
        return Crop.objects.all().select_related('farmer')
