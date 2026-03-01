"""Payments app views – Stripe Checkout + Webhook."""
import json
import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics

from orders.models import Order
from .models import PaymentLog
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsConsumer, IsAdminUser

stripe.api_key = settings.STRIPE_SECRET_KEY


class CreateCheckoutSessionView(APIView):
    """Create Stripe Checkout Session for an order."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get('order_id')
        try:
            order = Order.objects.get(id=order_id, payment_status='pending')
            # Only allow the consumer who owns it, OR the assigned delivery agent
            if request.user.role == 'consumer' and order.consumer != request.user:
                return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
            if request.user.role == 'delivery' and order.delivery_agent != request.user:
                return Response({'error': 'Order not assigned to you.'}, status=status.HTTP_403_FORBIDDEN)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found or already paid.'}, status=status.HTTP_404_NOT_FOUND)

        if order.total_price < 50:
            return Response({'error': 'Minimum order amount for Online Payment is ₹50 due to payment gateway limits. Please collect cash instead.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'inr',
                        'product_data': {
                            'name': order.crop.name,
                            'description': f'{order.quantity}kg of {order.crop.name}',
                        },
                        'unit_amount': int(order.total_price * 100),  # paise
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=f"{settings.FRONTEND_URL}/orders/success/?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.FRONTEND_URL}/cart/",
                metadata={
                    'order_id': str(order.id),
                    'consumer_id': str(order.consumer.id),
                }
            )
            # Save session ID to order
            order.stripe_session_id = session.id
            order.save()
            return Response({'checkout_url': session.url, 'session_id': session.id})
        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class VerifyCheckoutSessionView(APIView):
    """Verify Stripe Checkout Session manually (Fallback for when webhooks fail locally)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = request.data.get('session_id')
        if not session_id:
            return Response({'error': 'No session ID provided.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid':
                # Re-use webhook logic to update DB
                StripeWebhookView()._handle_successful_payment(session)
                
                # Check if it was successfully marked paid
                order_id = session.get('metadata', {}).get('order_id')
                if order_id:
                    from orders.models import Order
                    order = Order.objects.get(id=order_id)
                    # _handle_successful_payment already updates the status correctly.
                return Response({'message': 'Payment confirmed.', 'status': 'paid'})
            return Response({'message': 'Payment pending.', 'status': session.payment_status})
        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """Handle Stripe webhook events."""
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            return HttpResponse('Invalid payload', status=400)
        except stripe.error.SignatureVerificationError:
            return HttpResponse('Invalid signature', status=400)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            self._handle_successful_payment(session)

        return HttpResponse(status=200)

    def _handle_successful_payment(self, session):
        order_id = session.get('metadata', {}).get('order_id')
        if not order_id:
            return

        try:
            order = Order.objects.get(id=order_id)
            order.payment_status = 'paid'
            
            # If this is the initial consumer payment (status pending)
            if order.order_status == 'pending':
                order.order_status = 'confirmed'
                from django.utils import timezone
                from datetime import timedelta
                order.estimated_delivery_time = timezone.now() + timedelta(hours=2)
                from orders.utils import assign_delivery_agent
                assign_delivery_agent(order)
            elif order.payment_method == 'cod' and order.order_status in ['picked_up', 'out_for_delivery']:
                # The customer is paying via Stripe Link at the door.
                # Mark it as delivered automatically to save the agent a click!
                order.order_status = 'delivered'
                order.cod_payment_type = 'online'

            order.stripe_payment_id = session.get('payment_intent', '')
            order.save()

            # Create PaymentLog
            PaymentLog.objects.get_or_create(
                order=order,
                defaults={
                    'stripe_payment_id': session.get('payment_intent', session['id']),
                    'stripe_session_id': session['id'],
                    'amount': session.get('amount_total', 0) / 100,
                    'currency': session.get('currency', 'inr'),
                    'status': 'succeeded',
                }
            )
        except Order.DoesNotExist:
            pass


class PaymentLogListView(APIView):
    """View payment logs (and failed/cancelled orders) based on role."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        from orders.models import Order
        
        logs = []
        if user.role == 'admin' or user.is_superuser:
            qs_logs = PaymentLog.objects.filter(status='succeeded').select_related('order__consumer', 'order__crop')
            qs_paid = Order.objects.filter(payment_status='paid').select_related('consumer', 'crop')
        elif user.role == 'farmer':
            qs_logs = PaymentLog.objects.filter(status='succeeded', order__crop__farmer=user).select_related('order__consumer', 'order__crop')
            qs_paid = Order.objects.filter(crop__farmer=user, payment_status='paid').select_related('consumer', 'crop')
        else:
            qs_logs = PaymentLog.objects.filter(status='succeeded', order__consumer=user).select_related('order__consumer', 'order__crop')
            qs_paid = Order.objects.filter(consumer=user, payment_status='paid').select_related('consumer', 'crop')

        # Add successful/pending from PaymentLog
        for p in qs_logs:
            logs.append({
                'id': p.id,
                'order_id': p.order.id,
                'consumer_name': p.order.consumer.name,
                'crop_name': p.order.crop.name,
                'stripe_payment_id': p.stripe_payment_id,
                'amount': p.amount,
                'currency': p.currency,
                'status': p.status,
                'created_at': p.created_at
            })

        # Add successful/paid from Orders that don't have a PaymentLog (e.g. COD deliveries)
        existing_order_ids = set(p.order.id for p in qs_logs)
        for o in qs_paid:
            if o.id not in existing_order_ids:
                stripe_id_label = f"COD - {o.cod_payment_type.upper()}" if o.cod_payment_type else "COD"
                logs.append({
                    'id': f'cod_{o.id}',
                    'order_id': o.id,
                    'consumer_name': o.consumer.name,
                    'crop_name': o.crop.name,
                    'stripe_payment_id': stripe_id_label,
                    'amount': o.total_price,
                    'currency': 'inr',
                    'status': 'succeeded',
                    'created_at': o.updated_at or o.created_at
                })

        logs.sort(key=lambda x: x['created_at'], reverse=True)
        return Response({'results': logs})
