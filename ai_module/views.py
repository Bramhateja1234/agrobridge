"""AI Module views."""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .ml.price_model import predict_price
from .ml.demand_model import predict_demand


class PredictPriceView(APIView):
    """
    POST /api/predict-price/
    Body: { "crop_type": "grain", "season": "winter", "quantity": 100 }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        crop_type = request.data.get('crop_type', 'other')
        season = request.data.get('season', 'summer')
        quantity = request.data.get('quantity', 100)

        try:
            quantity = float(quantity)
        except (ValueError, TypeError):
            return Response({'error': 'quantity must be a number.'}, status=status.HTTP_400_BAD_REQUEST)

        predicted = predict_price(crop_type, season, quantity)
        return Response({
            'crop_type': crop_type,
            'season': season,
            'quantity_kg': quantity,
            'predicted_price_per_kg': predicted,
            'total_estimated_value': round(predicted * quantity, 2)
        })


class PredictDemandView(APIView):
    """
    POST /api/predict-demand/
    Body: { "crop_type": "grain", "periods": 3 }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        crop_type = request.data.get('crop_type', 'grain')
        periods = request.data.get('periods', 3)

        try:
            periods = int(periods)
            if periods < 1 or periods > 12:
                raise ValueError
        except (ValueError, TypeError):
            return Response({'error': 'periods must be an integer between 1 and 12.'}, status=status.HTTP_400_BAD_REQUEST)

        result = predict_demand(crop_type, periods)
        return Response(result)


from .gemini_service import GeminiService
from .external_services import WeatherService, NewsService
from rest_framework.decorators import api_view, permission_classes

@api_view(['POST'])
@permission_classes([AllowAny])
def crop_recommendation(request):
    """
    POST /api/crop-recommendation/
    Body: { "state": "...", "district": "...", "season": "...", "n": 50, "p": 30, "k": 40, "ph": 6.5, "temp": 28, "hum": 70, "rain": 1000 }
    """
    data = request.data
    prompt = f"""
    Recommend the best crop for these parameters in India:
    State: {data.get('state', 'Unknown')}
    District: {data.get('district', 'Unknown')}
    Season: {data.get('season', 'Unknown')}
    Soil: N={data.get('n', 0)}, P={data.get('p', 0)}, K={data.get('k', 0)}, pH={data.get('ph', 7)}
    Weather: Temp={data.get('temp', 25)}°C, Humidity={data.get('hum', 50)}%, Rainfall={data.get('rain', 800)}mm

    Return ONLY valid JSON:
    {{
        "recommended_crop": "Single Main Crop Name",
        "confidence": "percentage string (e.g. 92%)",
        "market_price": "estimated price in ₹/kg (e.g. 35)",
        "expected_yield": "estimated yield in kg/acre (e.g. 2500)",
        "recommendations": ["4-5 short bullet points of advice"],
        "reasoning": "short scientific explanation"
    }}
    """
    fallback = {
        "recommended_crop": "Gram",
        "confidence": "85%",
        "market_price": "35",
        "expected_yield": "2400",
        "recommendations": [
            "Ensure proper irrigation during dry spells",
            "Monitor soil pH levels regularly",
            "Apply organic fertilizers for better yield",
            "Consider crop rotation for soil health"
        ],
        "reasoning": "Based on balanced soil parameters and seasonal conditions."
    }
    service = GeminiService()
    result = service.generate_json(prompt, fallback)
    return Response(result)


@api_view(['POST'])
@permission_classes([AllowAny])
def fertilizer_advice(request):
    """
    POST /api/fertilizer-advice/
    Body: { "crop_name": "Wheat", "n": 50, "p": 30, "k": 40, "soil_health": "..." }
    """
    data = request.data
    prompt = f"""
    Provide professional fertilizer advice for:
    Crop Name: {data.get('crop_name', 'unknown')}
    Current Soil Levels: N={data.get('n', 0)}, P={data.get('p', 0)}, K={data.get('k', 0)}
    Soil Health/Condition: {data.get('soil_health', 'Normal')}

    Return ONLY valid JSON:
    {{
        "recommended_fertilizers": ["list of strings"],
        "application_method": "detailed string",
        "dosage": "specific dosage per acre",
        "expected_improvement": "string description",
        "precautions": ["list of strings"],
        "soil_analysis": "short scientific summary"
    }}
    """
    fallback = {
        "recommended_fertilizers": ["Urea", "DAP", "MOP"],
        "application_method": "Broadcasting during first irrigation",
        "dosage": "50kg Urea, 30kg DAP per acre",
        "expected_improvement": "Significant increase in grain weight and plant vigor",
        "precautions": ["Apply during cool hours", "Ensure soil moisture"],
        "soil_analysis": "Levels indicate slight nitrogen deficiency for the selected crop."
    }
    service = GeminiService()
    result = service.generate_json(prompt, fallback)
    return Response(result)


@api_view(['POST'])
@permission_classes([AllowAny])
def yield_prediction(request):
    """
    POST /api/yield-prediction/
    Body: { "crop_name": "Rice", "area_acres": 5, "rainfall_mm": 1200, "fertilizer_used": "Urea" }
    """
    data = request.data
    prompt = f"""
    Predict crop yield for:
    Crop Name: {data.get('crop_name', 'Rice')}
    Area (Acres): {data.get('area_acres', 1)}
    Rainfall (mm): {data.get('rainfall_mm', 1000)}
    Fertilizer Used: {data.get('fertilizer_used', 'standard')}

    Return ONLY valid JSON:
    {{
        "predicted_yield_tons": 0.0,
        "yield_category": "Average/High/Low",
        "environmental_factors": ["list of strings"],
        "optimization_tips": ["list of strings"]
    }}
    """
    fallback = {
        "predicted_yield_tons": 2.5,
        "yield_category": "Average",
        "environmental_factors": ["Standard rainfall", "Standard soil"],
        "optimization_tips": ["Improve irrigation", "Use balanced fertilization"]
    }
    service = GeminiService()
    result = service.generate_json(prompt, fallback)
    return Response(result)


@api_view(['POST'])
@permission_classes([AllowAny])
def rainfall_prediction(request):
    """
    POST /api/rainfall-prediction/
    Body: { "location": "Maharastra", "month": "July" }
    """
    data = request.data
    prompt = f"""
    Predict rainfall pattern for:
    Location: {data.get('location', 'India')}
    Month: {data.get('month', 'current monsoon')}

    Return ONLY valid JSON:
    {{
        "expected_rainfall_category": "Normal/Abnormal/Heavy/Drought",
        "estimated_mm": "range in mm",
        "impact_on_crops": "string description",
        "action_plan": ["list of strings"]
    }}
    """
    fallback = {
        "expected_rainfall_category": "Normal",
        "estimated_mm": "100-200mm",
        "impact_on_crops": "Suitable for most seasonal crops",
        "action_plan": ["Standard irrigation", "Ensure proper drainage"]
    }
    service = GeminiService()
    result = service.generate_json(prompt, fallback)
    return Response(result)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_weather_forecast(request):
    """
    GET /api/weather-forecast/?lat=...&lon=...
    """
    lat = request.query_params.get('lat')
    lon = request.query_params.get('lon')
    if not lat or not lon:
        return Response({'error': 'lat and lon are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    result = WeatherService.get_forecast(lat, lon)
    return Response(result)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_agri_news(request):
    """
    GET /api/agri-news/
    """
    result = NewsService.get_agri_news()
    return Response(result)
