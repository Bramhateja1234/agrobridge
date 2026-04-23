"""Orders app views."""
import logging
import threading
import time

from django.db import transaction
from django.db.models import Sum, Count
from django.utils.timezone import now
from datetime import timedelta

from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import Order, RefundLog, ALLOWED_CANCEL_STATUSES, DELIVERY_FEE, OrderStatus, PaymentStatus
from .serializers import OrderSerializer, PlaceOrderSerializer, RefundLogSerializer
from users.permissions import IsConsumer, IsFarmer, IsAdminUser, IsDeliveryAgent

logger = logging.getLogger(__name__)


# ── Async Refund Completion ───────────────────────────────────────────────────
def complete_refund_async(refund_log_id):
    """Simulate refund processing pipeline (runs in background thread)."""
    time.sleep(5)
    try:
        refund = RefundLog.objects.get(id=refund_log_id)
        if refund.status == 'pending':
            refund.status = 'completed'
            refund.save()
            # Mirror the status back on the parent order
            refund.order.refund_status = 'completed'
            refund.order.save(update_fields=['refund_status'])
            logger.info(f"Refund #{refund_log_id} auto-completed for Order #{refund.order_id} (amount ₹{refund.amount})")
    except RefundLog.DoesNotExist:
        logger.warning(f"Refund #{refund_log_id} not found during auto-completion")


class PlaceOrderView(APIView):
    """Consumer places an order – creates pending order before Stripe checkout."""
    permission_classes = [IsConsumer]

    def post(self, request):
        serializer = PlaceOrderSerializer(data=request.data)
        if serializer.is_valid():
            unreviewed_orders = Order.objects.filter(
                consumer=request.user,
                order_status='delivered',
                review__isnull=True
            ).exists()

            if unreviewed_orders:
                return Response(
                    {'error': 'You must review your previous delivered orders before placing a new one.', 'requires_review': True},
                    status=status.HTTP_400_BAD_REQUEST
                )

            payment_method = serializer.validated_data.get('payment_method', 'online')
            is_cod = (payment_method == 'cod')

            import uuid
            from django.contrib.auth import get_user_model
            from django.utils import timezone
            from datetime import timedelta as dt_timedelta
            import qrcode
            from io import BytesIO
            from django.core.files.base import ContentFile
            from .utils import assign_delivery_agent

            farmer = serializer.validated_data['crop'].farmer
            pickup_address = f"{farmer.name}'s Farm (Lat: {farmer.latitude}, Lng: {farmer.longitude})"

            order = Order.objects.create(
                consumer=request.user,
                crop=serializer.validated_data['crop'],
                quantity=serializer.validated_data['quantity'],
                total_price=serializer.validated_data['total_price'],
                payment_method=payment_method,
                payment_status=PaymentStatus.PENDING,
                order_status=OrderStatus.CONFIRMED if is_cod else OrderStatus.PENDING,
                delivery_address=serializer.validated_data.get('delivery_address', ''),
                pickup_address=pickup_address,
                delivery_latitude=serializer.validated_data.get('delivery_latitude'),
                delivery_longitude=serializer.validated_data.get('delivery_longitude'),
                estimated_delivery_time=timezone.now() + dt_timedelta(hours=2) if is_cod else None
            )

            if is_cod:
                assign_delivery_agent(order)

            def create_qr_file(data_str, prefix):
                qr = qrcode.QRCode(version=1, box_size=10, border=4)
                qr.add_data(data_str)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                return ContentFile(buffer.getvalue(), name=f"{prefix}_order_{order.id}.png")

            order.pickup_qr.save(f"pickup_{order.id}.png", create_qr_file(f"PICKUP-{order.id}", "pickup"), save=False)
            order.delivery_qr.save(f"delivery_{order.id}.png", create_qr_file(f"DELIVERY-{order.id}", "delivery"), save=False)
            order.save()

            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConsumerOrderHistoryView(generics.ListAPIView):
    """Consumer's own order history."""
    serializer_class = OrderSerializer
    permission_classes = [IsConsumer]

    def get_queryset(self):
        return Order.objects.filter(consumer=self.request.user).select_related('crop', 'crop__farmer')


class CancelOrderView(APIView):
    """Consumer cancels an order – atomic, idempotent, refund-safe."""
    permission_classes = [IsConsumer]

    def post(self, request, pk):
        idempotency_key = request.headers.get('Idempotency-Key', '').strip()

        with transaction.atomic():
            try:
                order = Order.objects.select_for_update().get(pk=pk, consumer=request.user)
            except Order.DoesNotExist:
                return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

            # --- Idempotency check ---
            if idempotency_key and order.idempotency_key == idempotency_key:
                return Response({
                    'message': 'Order already cancelled (duplicate request ignored).',
                    'refund_amount': float(order.refund_amount),
                }, status=status.HTTP_200_OK)

            # --- Double-cancellation guard ---
            if order.is_cancelled:
                return Response({'error': 'Order already cancelled.'}, status=status.HTTP_400_BAD_REQUEST)

            # --- State machine with descriptive reason ---
            if order.order_status not in ALLOWED_CANCEL_STATUSES:
                reason_map = {
                    OrderStatus.PICKED_UP: 'Order already picked up by delivery agent.',
                    OrderStatus.OUT_FOR_DELIVERY: 'Order is already out for delivery.',
                    OrderStatus.DELIVERED: 'Order has already been delivered.',
                }
                reason = reason_map.get(order.order_status, 'Cancellation window closed.')
                return Response({'error': reason}, status=status.HTTP_400_BAD_REQUEST)

            # --- Refund calculation ---
            refund_amount = 0
            if order.payment_status == PaymentStatus.PAID:
                refund_amount = max(float(order.total_price) - DELIVERY_FEE, 0)
                # Data consistency check
                assert abs(refund_amount + DELIVERY_FEE - float(order.total_price)) < 0.01, "Refund consistency error"
                order.refund_status = 'pending'
            else:
                order.refund_status = 'none'
                if order.payment_method == 'online' and order.payment_status == PaymentStatus.PENDING:
                    order.payment_status = PaymentStatus.FAILED

            order.refund_amount = refund_amount
            order.is_cancelled = True
            order.order_status = OrderStatus.CANCELLED
            order.cancelled_by = 'consumer'
            if idempotency_key:
                order.idempotency_key = idempotency_key
            order.save()

            refund_log = None
            if refund_amount > 0:
                refund_log = RefundLog.objects.create(
                    order=order,
                    amount=refund_amount,
                    delivery_fee=DELIVERY_FEE,
                    total_original=order.total_price,
                    status='pending',
                    cancelled_by='consumer',
                )
                logger.info(f"Refund created for Order #{order.id} – amount ₹{refund_amount}")

        # Launch async auto-completion outside the transaction
        if refund_log:
            threading.Thread(
                target=complete_refund_async,
                args=(refund_log.id,),
                daemon=True
            ).start()

        return Response({
            'message': 'Order cancelled successfully.',
            'refund_amount': refund_amount,
            'refund_status': order.refund_status,
        }, status=status.HTTP_200_OK)


class FarmerOrdersView(generics.ListAPIView):
    """Orders for crops belonging to the authenticated farmer."""
    serializer_class = OrderSerializer
    permission_classes = [IsFarmer]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin' or user.is_superuser:
            return Order.objects.all().select_related('crop', 'consumer')
        return Order.objects.filter(crop__farmer=user).select_related('crop', 'consumer')


class AdminOrderListView(generics.ListAPIView):
    """Admin: all orders."""
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]
    queryset = Order.objects.all().select_related('crop', 'consumer')


class AdminRefundLogView(generics.ListAPIView):
    """Admin: all refund log entries – single source of truth for refund history."""
    serializer_class = RefundLogSerializer
    permission_classes = [IsAdminUser]
    queryset = RefundLog.objects.all().select_related('order', 'order__consumer', 'order__crop')


class AdminCompleteRefundView(APIView):
    """Admin: manually mark a refund as completed."""
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        try:
            refund = RefundLog.objects.get(pk=pk)
        except RefundLog.DoesNotExist:
            return Response({'error': 'Refund log not found.'}, status=status.HTTP_404_NOT_FOUND)

        if refund.status == 'completed':
            return Response({'message': 'Already completed.'}, status=status.HTTP_200_OK)

        refund.status = 'completed'
        refund.save()
        refund.order.refund_status = 'completed'
        refund.order.save(update_fields=['refund_status'])

        logger.info(f"Admin manually completed Refund #{refund.id} for Order #{refund.order_id}")
        return Response({'message': 'Refund marked as completed.'}, status=status.HTTP_200_OK)


class AdminAnalyticsView(APIView):
    """Admin: 7-day refund trend and revenue data for dashboard charts."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        today = now().date()
        last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]

        refund_data, revenue_data = [], []
        for day in last_7_days:
            day_refunds = RefundLog.objects.filter(created_at__date=day)
            total_refund = day_refunds.aggregate(total=Sum('amount'))['total'] or 0
            net_revenue = day_refunds.count() * DELIVERY_FEE
            refund_data.append(float(total_refund))
            revenue_data.append(float(net_revenue))

        total_orders = Order.objects.count()
        cancelled_paid = Order.objects.filter(is_cancelled=True, payment_status=PaymentStatus.PAID).count()
        refund_rate = round((cancelled_paid / total_orders * 100), 1) if total_orders else 0

        today_refunds = RefundLog.objects.filter(created_at__date=today)
        total_today = today_refunds.aggregate(total=Sum('amount'))['total'] or 0

        return Response({
            'dates': [d.strftime('%d %b') for d in last_7_days],
            'refunds': refund_data,
            'revenue': revenue_data,
            'refund_rate': refund_rate,
            'total_refunds_today': float(total_today),
            'cancelled_paid_count': cancelled_paid,
        })


class DeliveryAgentOrderListView(generics.ListAPIView):
    """Delivery Agent: orders assigned to this agent (excludes cancelled)."""
    serializer_class = OrderSerializer
    permission_classes = [IsDeliveryAgent]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin' or user.is_superuser:
            return Order.objects.all().select_related('crop', 'consumer')
        return Order.objects.filter(
            delivery_agent=user
        ).exclude(
            order_status=OrderStatus.CANCELLED
        ).select_related('crop', 'consumer')


def validate_qr(scanned_qr, order_id):
    scanned_qr = scanned_qr.strip().lower()
    if "/" in scanned_qr:
        scanned_qr = scanned_qr.split("/")[-1]
    return str(order_id) in scanned_qr


class UpdateOrderStatusView(APIView):
    """Delivery Agent or Admin: update the delivery status of an order."""
    permission_classes = [IsDeliveryAgent]

    def patch(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('order_status')
        scanned_qr = request.data.get('scanned_qr')

        if scanned_qr:
            if not validate_qr(scanned_qr, order.id):
                return Response({"error": f"Invalid QR Code for order {order.id}"}, status=status.HTTP_400_BAD_REQUEST)

        valid_statuses = [s.value for s in OrderStatus if s != OrderStatus.CANCELLED]
        if new_status not in valid_statuses:
            return Response({'error': 'Invalid status.'}, status=status.HTTP_400_BAD_REQUEST)

        if new_status == OrderStatus.PICKED_UP and order.order_status != OrderStatus.CONFIRMED:
            return Response({"error": "Order not ready for pickup"}, status=status.HTTP_400_BAD_REQUEST)

        if request.user.role == 'delivery':
            if order.delivery_agent is None:
                order.delivery_agent = request.user
            elif order.delivery_agent != request.user:
                return Response({'error': 'This order is assigned to another agent.'}, status=status.HTTP_403_FORBIDDEN)

        cod_payment_type = request.data.get('cod_payment_type')
        if cod_payment_type in ['cash', 'online'] and order.payment_method == 'cod':
            order.cod_payment_type = cod_payment_type

        order.order_status = new_status
        order.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)


class UpdateOrderLocationView(APIView):
    """Simulate GPS tracking by incrementing coordinates."""
    permission_classes = [IsDeliveryAgent]

    def patch(self, request, pk):
        try:
            order = Order.objects.get(pk=pk, delivery_agent=request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found or not assigned to you.'}, status=status.HTTP_404_NOT_FOUND)

        if order.order_status not in [OrderStatus.PICKED_UP, OrderStatus.OUT_FOR_DELIVERY]:
            return Response({'error': 'Location can only be updated while in transit.'}, status=status.HTTP_400_BAD_REQUEST)

        if order.delivery_latitude and order.delivery_longitude:
            order.delivery_latitude += 0.0005
            order.delivery_longitude += 0.0005
        else:
            order.delivery_latitude = 28.6139
            order.delivery_longitude = 77.2090

        order.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)


class DeliveryAgentStatsView(APIView):
    """Delivery Agent stats (completed, active, cancelled)."""
    permission_classes = [IsDeliveryAgent]

    def get(self, request):
        user = request.user
        qs = Order.objects.filter(delivery_agent=user)
        return Response({
            'delivered': qs.filter(order_status=OrderStatus.DELIVERED).count(),
            'active': qs.filter(order_status__in=[OrderStatus.PICKED_UP, OrderStatus.OUT_FOR_DELIVERY]).count(),
            'total_assigned': qs.count(),
            'cancelled': qs.filter(order_status=OrderStatus.CANCELLED).count(),
            'history': OrderSerializer(qs.order_by('-updated_at')[:20], many=True).data
        })
