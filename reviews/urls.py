"""Reviews URL patterns."""
from django.urls import path
from . import views

urlpatterns = [
    path('submit/', views.SubmitReviewView.as_view(), name='submit-review'),
    path('farmer/<int:farmer_id>/', views.FarmerReviewsView.as_view(), name='farmer-reviews'),
    path('crop/<int:crop_id>/', views.CropReviewsView.as_view(), name='crop-reviews'),
    path('admin/all/', views.AdminAllReviewsView.as_view(), name='admin-reviews'),
    path('admin/<int:pk>/moderate/', views.AdminModerateReviewView.as_view(), name='moderate-review'),
]
