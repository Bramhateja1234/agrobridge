"""Payments URL patterns."""
from django.urls import path
from . import views

urlpatterns = [
    path('checkout/', views.CreateCheckoutSessionView.as_view(), name='create-checkout'),
    path('verify/', views.VerifyCheckoutSessionView.as_view(), name='verify-checkout'),
    path('webhook/', views.StripeWebhookView.as_view(), name='stripe-webhook'),
    path('logs/', views.PaymentLogListView.as_view(), name='payment-logs'),
]
