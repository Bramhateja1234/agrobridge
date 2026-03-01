"""Utility functions for orders."""
from django.db.models import Count, Q
from django.contrib.auth import get_user_model

def assign_delivery_agent(order):
    """
    Finds the delivery agent with the least number of active deliveries
    and assigns them to the given order.
    An active delivery is one that is not delivered or cancelled.
    """
    User = get_user_model()
    
    # Get all delivery agents
    agents = User.objects.filter(role='delivery', is_active=True)
    if not agents.exists():
        return None

    # Annotate agents with their count of active orders
    agents_with_counts = agents.annotate(
        active_order_count=Count(
            'assigned_deliveries', 
            filter=~Q(assigned_deliveries__order_status__in=['delivered', 'cancelled'])
        )
    ).order_by('active_order_count', 'id')

    # Pick the one with the lowest count
    choicest_agent = agents_with_counts.first()
    
    if choicest_agent:
        order.delivery_agent = choicest_agent
        order.save(update_fields=['delivery_agent'])
        return choicest_agent
    return None
