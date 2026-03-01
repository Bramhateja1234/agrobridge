"""Users app URL patterns."""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/block/', views.UserBlockView.as_view(), name='user-block'),
    path('users/<int:pk>/verify/', views.UserVerifyView.as_view(), name='user-verify'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user-delete'),
    path('otp/send/', views.OTPSendView.as_view(), name='otp-send'),
    path('otp/verify/', views.OTPVerifyView.as_view(), name='otp-verify'),
    path('password/reset/', views.PasswordResetView.as_view(), name='password-reset'),
]
