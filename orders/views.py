"""Orders app views."""
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import Order
from .models import Order
from .serializers import OrderSerializer, PlaceOrderSerializer
from users.permissions import IsConsumer, IsFarmer, IsAdminUser, IsDeliveryAgent


class PlaceOrderView(APIView):
    """Consumer places an order – creates pending order before Stripe checkout."""
    permission_classes = [IsConsumer]

    def post(self, request):
        serializer = PlaceOrderSerializer(data=request.data)
        if serializer.is_valid():
            # Check for unreviewed delivered orders
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
            User = get_user_model()
            from django.utils import timezone
            from datetime import timedelta
            import qrcode
            from io import BytesIO
            from django.core.files.base import ContentFile
            
            from .utils import assign_delivery_agent
            
            # Farmer's address (assuming farmer has basic latitude/longitude and name/phone, we will just use a dummy text address based on farmer for pickup_address since Farmer model doesn't have an address field currently, or use farmer's coordinate string)
            farmer = serializer.validated_data['crop'].farmer
            pickup_address = f"{farmer.name}'s Farm (Lat: {farmer.latitude}, Lng: {farmer.longitude})"
            
            order = Order.objects.create(
                consumer=request.user,
                crop=serializer.validated_data['crop'],
                quantity=serializer.validated_data['quantity'],
                total_price=serializer.validated_data['total_price'],
                payment_method=payment_method,
                payment_status='pending',
                order_status='confirmed' if is_cod else 'pending',
                delivery_address=serializer.validated_data.get('delivery_address', ''),
                pickup_address=pickup_address,
                delivery_latitude=serializer.validated_data.get('delivery_latitude'),
                delivery_longitude=serializer.validated_data.get('delivery_longitude'),
                estimated_delivery_time=timezone.now() + timedelta(hours=2) if is_cod else None
            )

            # Auto-assign delivery agent immediately if COD
            if is_cod:
                assign_delivery_agent(order)

            # Generate Python QR Codes
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
    """Consumer cancels an order."""
    permission_classes = [IsConsumer]

    def post(self, request, pk):
        try:
            order = Order.objects.get(pk=pk, consumer=request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        if order.order_status not in ['pending', 'confirmed']:
            return Response({'error': 'Only pending or confirmed orders can be cancelled.'}, status=status.HTTP_400_BAD_REQUEST)

        order.order_status = 'cancelled'
        order.payment_status = 'failed' if order.payment_method == 'online' and order.payment_status == 'pending' else order.payment_status
        order.save()
        return Response({'message': 'Order cancelled successfully.'}, status=status.HTTP_200_OK)


class FarmerOrdersView(generics.ListAPIView):
    """Orders for crops belonging to the authenticated farmer."""
    serializer_class = OrderSerializer
    permission_classes = [IsFarmer]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin' or user.is_superuser:
            return Order.objects.all().select_related('crop', 'consumer')
        return Order.objects.filter(
            crop__farmer=user
        ).select_related('crop', 'consumer')


class AdminOrderListView(generics.ListAPIView):
    """Admin: all orders."""
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]
    queryset = Order.objects.all().select_related('crop', 'consumer')

class DeliveryAgentOrderListView(generics.ListAPIView):
    """Delivery Agent: viewing orders to assign or already assigned."""
    serializer_class = OrderSerializer
    permission_classes = [IsDeliveryAgent]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin' or user.is_superuser:
            return Order.objects.all().select_related('crop', 'consumer')
        # Only return orders strictly assigned to this agent
        return Order.objects.filter(
            delivery_agent=user
        ).select_related('crop', 'consumer')

class UpdateOrderStatusView(APIView):
    """Delivery Agent or Admin: update the delivery status of an order."""
    permission_classes = [IsDeliveryAgent]

    def patch(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('order_status')
        valid_statuses = ['confirmed', 'picked_up', 'out_for_delivery', 'delivered', 'cancelled']
        
        if new_status not in valid_statuses:
            return Response({'error': 'Invalid status.'}, status=status.HTTP_400_BAD_REQUEST)

        # For delivery agents, automatically assign if not assigned and they are taking it
        if request.user.role == 'delivery':
            if order.delivery_agent is None:
                order.delivery_agent = request.user
            elif order.delivery_agent != request.user:
                return Response({'error': 'This order is assigned to another agent.'}, status=status.HTTP_403_FORBIDDEN)

        cod_payment_type = request.data.get('cod_payment_type')
        if cod_payment_type in ['cash', 'online'] and order.payment_method == 'cod':
            order.cod_payment_type = cod_payment_type

        order.order_status = new_status
        order.save() # This triggers the COD -> paid auto-update from models.py

        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)


class UpdateOrderLocationView(APIView):
    """Simulate GPS tracking by incrementing coordinates."""
    permission_classes = [IsDeliveryAgent]

    def patch(self, request, pk):
        try:
            order = Order.objects.get(pk=pk, delivery_agent=request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found or not assigned to you.'}, status=status.HTTP_404_NOT_FOUND)

        if order.order_status not in ['picked_up', 'out_for_delivery']:
            return Response({'error': 'Location can only be updated while in transit.'}, status=status.HTTP_400_BAD_REQUEST)

        # Simulate movement
        if order.delivery_latitude and order.delivery_longitude:
            order.delivery_latitude += 0.0005
            order.delivery_longitude += 0.0005
        else:
            # Fallback coordinates if none exist
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
            'delivered': qs.filter(order_status='delivered').count(),
            'active': qs.filter(order_status__in=['picked_up', 'out_for_delivery']).count(),
            'total_assigned': qs.count(),
            'cancelled': qs.filter(order_status='cancelled').count(),
            'history': OrderSerializer(qs.order_by('-updated_at')[:20], many=True).data
        })
