"""Users app views."""
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser
from .serializers import (
    RegisterSerializer, LoginSerializer, UserProfileSerializer, AdminUserSerializer,
    OTPSendSerializer, OTPVerifySerializer
)
from .permissions import IsAdminUser
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


# Mock OTP storage (use Redis/cache in production)
OTP_STORE = {}


class OTPSendView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPSendSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            otp = str(random.randint(100000, 999999))
            OTP_STORE[phone] = otp
            # In production: send SMS via Twilio/Fast2SMS
            print(f"[MOCK OTP] Phone: {phone}, OTP: {otp}")
            return Response({'message': f'OTP sent to {phone} (mock mode).', 'otp': otp})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OTPVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            otp = serializer.validated_data['otp']
            stored = OTP_STORE.get(phone)
            if stored == otp:
                del OTP_STORE[phone]
                try:
                    user = CustomUser.objects.get(phone=phone)
                    user.is_verified = True
                    user.save()
                    token_data = get_tokens_for_user(user)
                    return Response({'message': 'OTP verified.', **token_data})
                except CustomUser.DoesNotExist:
                    return Response({'error': 'No user with this phone.'}, status=status.HTTP_404_NOT_FOUND)
            return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from .serializers import PasswordResetSerializer
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            otp = serializer.validated_data['otp']
            new_password = serializer.validated_data['new_password']
            
            stored = OTP_STORE.get(phone)
            if stored and stored == otp:
                try:
                    user = CustomUser.objects.get(phone=phone)
                    user.set_password(new_password)
                    user.save()
                    del OTP_STORE[phone]
                    return Response({'message': 'Password reset successfully!'})
                except CustomUser.DoesNotExist:
                    return Response({'error': 'No account found with this phone number.'}, status=status.HTTP_404_NOT_FOUND)
            return Response({'error': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
