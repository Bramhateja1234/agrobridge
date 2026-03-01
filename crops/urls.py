"""Crops app URL patterns (API)."""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.CropListView.as_view(), name='crop-list'),
    path('<int:pk>/', views.CropDetailView.as_view(), name='crop-detail'),
    path('create/', views.CropCreateView.as_view(), name='crop-create'),
    path('<int:pk>/update/', views.CropUpdateView.as_view(), name='crop-update'),
    path('<int:pk>/delete/', views.CropDeleteView.as_view(), name='crop-delete'),
    path('my/', views.FarmerCropListView.as_view(), name='farmer-crops'),
    path('admin/all/', views.AllCropsAdminView.as_view(), name='admin-all-crops'),
]
