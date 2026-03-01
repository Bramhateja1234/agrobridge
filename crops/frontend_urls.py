"""Frontend template views for AgroBridge."""
from django.views.generic import TemplateView
from django.urls import path
from django.shortcuts import render


def home(request): return render(request, 'home.html')
def login_page(request): return render(request, 'auth/login.html')
def register_page(request): return render(request, 'auth/register.html')
def farmer_dashboard(request): return render(request, 'farmer/dashboard.html')
def browse_crops(request): return render(request, 'consumer/browse.html')
def cart_page(request): return render(request, 'consumer/cart.html')
def order_history(request): return render(request, 'consumer/order_history.html')
def profile_page(request): return render(request, 'auth/profile.html')

def order_success(request): return render(request, 'consumer/order_success.html')

def delivery_dashboard(request): return render(request, 'delivery/dashboard.html')


urlpatterns = [
    path('', home, name='home'),
    path('auth/login/', login_page, name='login-page'),
    path('auth/register/', register_page, name='register-page'),
    path('profile/', profile_page, name='profile-page'),
    path('farmer/dashboard/', farmer_dashboard, name='farmer-dashboard'),
    path('browse/', browse_crops, name='browse-crops'),
    path('cart/', cart_page, name='cart-page'),
    path('orders/', order_history, name='order-history'),
    path('orders/success/', order_success, name='order-success'),
    path('delivery/dashboard/', delivery_dashboard, name='delivery-dashboard'),
]
