"""Users app serializers."""
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    phone = serializers.CharField(required=True)
    state = serializers.CharField(required=True)
    country = serializers.CharField(required=True)
    address_line = serializers.CharField(required=True)

    class Meta:
        model = CustomUser
        fields = ['name', 'email', 'phone', 'state', 'country', 'address_line',
                  'password', 'password_confirm', 'role', 'latitude', 'longitude']

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        user = authenticate(username=attrs['email'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError('Invalid email or password.')
        if not user.is_active:
            raise serializers.ValidationError('User account is disabled.')
        attrs['user'] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    profile_photo_url = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            # Identity
            'id', 'name', 'email', 'phone', 'role', 'bio',
            'profile_photo', 'profile_photo_url',
            # Location
            'village', 'mandal', 'district',
            'address_line', 'city', 'state', 'country', 'pin_code',
            'latitude', 'longitude',
            # Farmer-specific
            'land_size_acres', 'soil_type', 'farming_type', 'crops_grown',
            # Delivery-specific
            'vehicle_type', 'license_number', 'is_available',
            # Account
            'is_verified', 'created_at',
        ]
        read_only_fields = ['id', 'role', 'is_verified', 'created_at', 'profile_photo_url']
        extra_kwargs = {
            'profile_photo': {'write_only': True},
        }

    def get_profile_photo_url(self, obj):
        request = self.context.get('request')
        if obj.profile_photo and request:
            return request.build_absolute_uri(obj.profile_photo.url)
        elif obj.profile_photo:
            return obj.profile_photo.url
        return None


class ProfilePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['profile_photo']


class AdminUserSerializer(UserProfileSerializer):
    class Meta(UserProfileSerializer.Meta):
        read_only_fields = list(UserProfileSerializer.Meta.read_only_fields) + ['password']


class OTPSendSerializer(serializers.Serializer):
    email = serializers.EmailField()


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=8)
