"""AI Module URL patterns."""
from django.urls import path
from . import views

urlpatterns = [
    path('predict-price/', views.PredictPriceView.as_view(), name='predict-price'),
    path('predict-demand/', views.PredictDemandView.as_view(), name='predict-demand'),
    
    # New Gemini & External API Endpoints
    path('crop-recommendation/', views.crop_recommendation, name='crop-recommendation'),
    path('fertilizer-advice/', views.fertilizer_advice, name='fertilizer-advice'),
    path('yield-prediction/', views.yield_prediction, name='yield-prediction'),
    path('rainfall-prediction/', views.rainfall_prediction, name='rainfall-prediction'),
    path('weather-forecast/', views.get_weather_forecast, name='weather-forecast'),
    path('agri-news/', views.get_agri_news, name='agri-news'),
]
