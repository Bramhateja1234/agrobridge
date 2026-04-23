"""Users app views."""
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser

from .models import CustomUser, OTPVerification
from .serializers import (
    RegisterSerializer, LoginSerializer, UserProfileSerializer, AdminUserSerializer,
    ProfilePhotoSerializer, OTPSendSerializer, OTPVerifySerializer
)
from .permissions import IsAdminUser
from .utils import send_email_otp
from django.utils import timezone
from datetime import timedelta
import random


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'profile_photo_url': user.profile_photo.url if user.profile_photo else None,
        }
    }


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token_data = get_tokens_for_user(user)
            return Response({
                'message': 'Registration successful.',
                **token_data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token_data = get_tokens_for_user(user)
            return Response({
                'message': 'Login successful.',
                **token_data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'error': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx


class ProfilePhotoView(APIView):
    """POST /api/auth/profile/photo/ — upload profile photo."""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = ProfilePhotoSerializer(
            request.user, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            photo_url = None
            if request.user.profile_photo:
                photo_url = request.build_absolute_uri(request.user.profile_photo.url)
            return Response({
                'message': 'Profile photo updated.',
                'profile_photo_url': photo_url,
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """DELETE /api/auth/profile/photo/ — remove profile photo."""
        if request.user.profile_photo:
            request.user.profile_photo.delete(save=True)
            return Response({'message': 'Profile photo removed.'})
        return Response({'message': 'No profile photo found.'}, status=status.HTTP_404_NOT_FOUND)


class ProfileStatsView(APIView):
    """GET /api/auth/profile/stats/ — aggregated stats for the logged-in user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        stats = {}

        if user.role == 'farmer':
            from orders.models import Order
            from reviews.models import Review
            # Orders received on farmer's crops
            farmer_orders = Order.objects.filter(crop__farmer=user)
            total_orders = farmer_orders.count()
            paid_orders = farmer_orders.filter(payment_status='paid')
            total_earnings = sum(float(o.total_price or 0) for o in paid_orders)
            delivered = farmer_orders.filter(order_status='delivered').count()
            # Rating
            try:
                rev = Review.objects.filter(farmer=user)
                avg_rating = sum(r.rating for r in rev) / rev.count() if rev.count() else 0
                rating_count = rev.count()
            except Exception:
                avg_rating = 0
                rating_count = 0
            # Crops
            crop_count = user.crops.count()
            stats = {
                'role': 'farmer',
                'total_orders': total_orders,
                'total_earnings': round(total_earnings, 2),
                'delivered_orders': delivered,
                'pending_orders': farmer_orders.filter(order_status='pending').count(),
                'crop_count': crop_count,
                'avg_rating': round(avg_rating, 1),
                'rating_count': rating_count,
            }

        elif user.role == 'consumer':
            from orders.models import Order
            consumer_orders = Order.objects.filter(consumer=user)
            total_spent = sum(float(o.total_price or 0)
                              for o in consumer_orders.filter(payment_status='paid'))
            stats = {
                'role': 'consumer',
                'total_orders': consumer_orders.count(),
                'delivered_orders': consumer_orders.filter(order_status='delivered').count(),
                'pending_orders': consumer_orders.filter(order_status='pending').count(),
                'cancelled_orders': consumer_orders.filter(order_status='cancelled').count(),
                'total_spent': round(total_spent, 2),
            }

        elif user.role == 'delivery':
            from orders.models import Order
            deliveries = Order.objects.filter(delivery_agent=user)
            completed = deliveries.filter(order_status='delivered').count()
            earnings = sum(
                float(o.total_price or 0) * 0.05
                for o in deliveries.filter(order_status='delivered')
            )
            stats = {
                'role': 'delivery',
                'total_deliveries': deliveries.count(),
                'completed_deliveries': completed,
                'pending_deliveries': deliveries.exclude(order_status='delivered').count(),
                'estimated_earnings': round(earnings, 2),
                'is_available': user.is_available,
            }

        elif user.role == 'admin':
            from orders.models import Order
            total_users = CustomUser.objects.count()
            pending_verifications = CustomUser.objects.filter(is_verified=False, role='farmer').count()
            active_deliveries = Order.objects.exclude(order_status__in=['delivered', 'cancelled']).count()
            stats = {
                'role': 'admin',
                'total_users': total_users,
                'pending_verifications': pending_verifications,
                'active_deliveries': active_deliveries,
                'platform_sales': round(sum(float(o.total_price or 0) for o in Order.objects.filter(payment_status='paid')), 2),
            }

        return Response(stats)


class UserListView(generics.ListAPIView):
    """Admin: list all users."""
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]
    queryset = CustomUser.objects.all()


class UserBlockView(APIView):
    """Admin: block/unblock a user."""
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        try:
            user = CustomUser.objects.get(pk=pk)
            user.is_active = not user.is_active
            user.save()
            action = 'blocked' if not user.is_active else 'unblocked'
            return Response({'message': f'User {action} successfully.'})
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)


class UserVerifyView(APIView):
    """Admin: explicitly verify a user account."""
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        try:
            user = CustomUser.objects.get(pk=pk)
            if user.is_verified:
                return Response({'message': 'User is already verified.'})
            user.is_verified = True
            user.save()
            return Response({'message': 'User verified successfully.'})
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)


class UserDeleteView(APIView):
    """Admin: explicitly delete a user account."""
    permission_classes = [IsAdminUser]

    def delete(self, request, pk):
        try:
            user = CustomUser.objects.get(pk=pk)
            if user.is_superuser:
                return Response({'error': 'Cannot delete superuser.'}, status=status.HTTP_400_BAD_REQUEST)
            user.delete()
            return Response({'message': 'User deleted successfully.'})
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)


class OTPSendView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPSendSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            last_otp = OTPVerification.objects.filter(email=email).order_by('-created_at').first()
            if last_otp and timezone.now() - last_otp.created_at < timedelta(minutes=1):
                return Response(
                    {'error': 'Please wait 1 minute before requesting another OTP.'},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            otp = str(random.randint(100000, 999999))
            OTPVerification.objects.create(email=email, otp=otp)
            res = send_email_otp(email, otp)
            if not res.get('success'):
                return Response(
                    {'error': 'Failed to send OTP via email.', 'details': res.get('message')},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            return Response({'message': 'OTP sent successfully.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OTPVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            otp_obj = OTPVerification.objects.filter(email=email).order_by('-created_at').first()
            if not otp_obj:
                return Response({'error': 'No OTP requested for this email.'}, status=status.HTTP_400_BAD_REQUEST)
            if timezone.now() - otp_obj.created_at > timedelta(minutes=5):
                return Response({'error': 'OTP expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)
            if otp_obj.attempts >= 3:
                return Response(
                    {'error': 'Maximum attempts exceeded. Please request a new OTP.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if otp_obj.otp == otp:
                otp_obj.delete()
                try:
                    user = CustomUser.objects.get(email=email)
                    user.is_verified = True
                    user.save()
                    token_data = get_tokens_for_user(user)
                    return Response({'message': 'OTP verified.', **token_data})
                except CustomUser.DoesNotExist:
                    return Response({'message': 'OTP verified.'})
            else:
                otp_obj.attempts += 1
                otp_obj.save()
                return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from .serializers import PasswordResetSerializer
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            new_password = serializer.validated_data['new_password']
            otp_obj = OTPVerification.objects.filter(email=email).order_by('-created_at').first()
            if not otp_obj:
                return Response({'error': 'No OTP requested for this email.'}, status=status.HTTP_400_BAD_REQUEST)
            if timezone.now() - otp_obj.created_at > timedelta(minutes=5):
                return Response({'error': 'OTP expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)
            if otp_obj.attempts >= 3:
                return Response(
                    {'error': 'Maximum attempts exceeded. Please request a new OTP.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if otp_obj.otp == otp:
                try:
                    user = CustomUser.objects.get(email=email)
                    user.set_password(new_password)
                    user.save()
                    otp_obj.delete()
                    return Response({'message': 'Password reset successfully!'})
                except CustomUser.DoesNotExist:
                    return Response(
                        {'error': 'No account found with this email address.'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                otp_obj.attempts += 1
                otp_obj.save()
                return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
