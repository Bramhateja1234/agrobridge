"""Frontend template views for AgroBridge."""
from django.views.generic import TemplateView
from django.urls import path
from django.shortcuts import render
from django.conf import settings


def home(request): return render(request, 'home.html')
def login_page(request): return render(request, 'auth/login.html')
def register_page(request): return render(request, 'auth/register.html')
def farmer_dashboard(request):
    return render(request, 'farmer/dashboard.html', {
        'openweather_key': getattr(settings, 'OPENWEATHER_API_KEY', ''),
    })
def browse_crops(request): return render(request, 'consumer/browse.html')
def cart_page(request): return render(request, 'consumer/cart.html')
def order_history(request): return render(request, 'consumer/order_history.html')
def consumer_dashboard(request): return render(request, 'consumer/dashboard.html')
def consumer_profile(request): return render(request, 'consumer/profile.html')
def profile_page(request): return render(request, 'auth/profile.html')

def order_success(request): return render(request, 'consumer/order_success.html')

def delivery_dashboard(request): return render(request, 'delivery/dashboard.html')
def delivery_profile(request): return render(request, 'delivery/profile.html')


urlpatterns = [
    path('', home, name='home'),
    path('auth/login/', login_page, name='login-page'),
    path('auth/register/', register_page, name='register-page'),
    path('profile/', profile_page, name='profile-page'),
    path('farmer/dashboard/', farmer_dashboard, name='farmer-dashboard'),
    path('browse/', browse_crops, name='browse-crops'),
    path('cart/', cart_page, name='cart-page'),
    path('orders/', order_history, name='order-history'),
    path('consumer/dashboard/', consumer_dashboard, name='consumer-dashboard'),
    path('consumer/profile/', consumer_profile, name='consumer-profile'),
    path('orders/success/', order_success, name='order-success'),
    path('delivery/dashboard/', delivery_dashboard, name='delivery-dashboard'),
    path('delivery/profile/', delivery_profile, name='delivery-profile'),
]
