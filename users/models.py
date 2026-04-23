"""Users app models."""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('farmer', 'Farmer'),
        ('consumer', 'Consumer'),
        ('admin', 'Admin'),
        ('delivery', 'Delivery Agent'),
    ]

    SOIL_TYPE_CHOICES = [
        ('loamy', 'Loamy'),
        ('sandy', 'Sandy'),
        ('clay', 'Clay'),
        ('black', 'Black Cotton'),
        ('red', 'Red Laterite'),
        ('alluvial', 'Alluvial'),
    ]

    FARMING_TYPE_CHOICES = [
        ('organic', 'Organic'),
        ('non_organic', 'Non-Organic'),
        ('mixed', 'Mixed'),
    ]

    VEHICLE_TYPE_CHOICES = [
        ('bike', 'Bike'),
        ('auto', 'Auto'),
        ('van', 'Van'),
        ('truck', 'Truck'),
    ]

    # ── Basic Identity ─────────────────────────────────────────────
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='consumer')
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    # ── Location ───────────────────────────────────────────────────
    village = models.CharField(max_length=100, blank=True, null=True)
    mandal = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    address_line = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    pin_code = models.CharField(max_length=20, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    # ── Farmer-Specific ────────────────────────────────────────────
    land_size_acres = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    soil_type = models.CharField(max_length=20, choices=SOIL_TYPE_CHOICES, blank=True, null=True)
    farming_type = models.CharField(max_length=15, choices=FARMING_TYPE_CHOICES, blank=True, null=True)
    crops_grown = models.TextField(blank=True, null=True, help_text='Comma-separated crop names')

    # ── Delivery-Specific ──────────────────────────────────────────
    vehicle_type = models.CharField(max_length=10, choices=VEHICLE_TYPE_CHOICES, blank=True, null=True)
    license_number = models.CharField(max_length=50, blank=True, null=True)
    is_available = models.BooleanField(default=True)

    # ── Account ────────────────────────────────────────────────────
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.role})"


class OTPVerification(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    attempts = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'OTP Verification'
        verbose_name_plural = 'OTP Verifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP for {self.email}"
