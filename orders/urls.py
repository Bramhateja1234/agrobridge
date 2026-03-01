"""Orders URL patterns."""
from django.urls import path
from . import views

urlpatterns = [
    path('place/', views.PlaceOrderView.as_view(), name='place-order'),
    path('my/', views.ConsumerOrderHistoryView.as_view(), name='consumer-orders'),
    path('<int:pk>/cancel/', views.CancelOrderView.as_view(), name='cancel-order'),
    path('received/', views.FarmerOrdersView.as_view(), name='farmer-orders'),
    path('admin/all/', views.AdminOrderListView.as_view(), name='admin-orders'),
    path('delivery/orders/', views.DeliveryAgentOrderListView.as_view(), name='delivery-orders'),
    path('delivery/stats/', views.DeliveryAgentStatsView.as_view(), name='delivery-stats'),
    path('<int:pk>/status/', views.UpdateOrderStatusView.as_view(), name='update-order-status'),
    path('<int:pk>/location/', views.UpdateOrderLocationView.as_view(), name='update-order-location'),
]
