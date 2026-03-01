import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class WeatherService:
    @staticmethod
    def get_forecast(lat, lon):
        api_key = getattr(settings, 'OPENWEATHER_API_KEY', None)
        if not api_key:
            return {"error": "Weather service API key not configured"}
        
        try:
            # Using 5-day / 3-hour forecast API
            url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Weather API error: {str(e)}")
            return {"error": "Weather service unavailable"}

class NewsService:
    @staticmethod
    def get_agri_news():
        api_key = getattr(settings, 'NEWS_API_KEY', None)
        if not api_key:
            return {"error": "News service API key not configured"}
        
        try:
            # Searching for agriculture in India
            url = f"https://newsapi.org/v2/everything?q=agriculture+india&language=en&sortBy=publishedAt&pageSize=10&apiKey={api_key}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"News API error: {str(e)}")
            return {"error": "News service unavailable"}
