"""AI Module: Demand Forecasting using Moving Average."""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Mock historical demand data (monthly sales per crop type in kg)
MOCK_DEMAND_DATA = {
    'grain': [1200, 1350, 1100, 1400, 1300, 1250, 1500, 1450, 1200, 1350, 1400, 1300],
    'vegetable': [800, 750, 900, 1000, 850, 780, 920, 870, 800, 750, 820, 860],
    'fruit': [600, 550, 700, 900, 1100, 1000, 800, 750, 650, 600, 580, 620],
    'pulse': [400, 420, 380, 440, 460, 410, 390, 430, 445, 415, 400, 420],
    'oilseed': [300, 280, 320, 310, 290, 300, 315, 305, 295, 310, 320, 300],
    'spice': [150, 160, 140, 155, 165, 145, 158, 162, 148, 155, 160, 152],
    'other': [200, 210, 195, 215, 205, 200, 212, 208, 198, 205, 210, 202],
}


def moving_average_forecast(data: list, window: int = 3, periods: int = 3) -> list:
    """Forecast next N periods using simple moving average."""
    result = list(data)
    for _ in range(periods):
        ma = sum(result[-window:]) / window
        result.append(round(ma, 2))
    return result[-periods:]


def predict_demand(crop_type: str, periods: int = 3) -> dict:
    """
    Predict demand for the next N months.
    Returns predicted values and month labels.
    """
    if crop_type not in MOCK_DEMAND_DATA:
        crop_type = 'other'

    historical = MOCK_DEMAND_DATA[crop_type]
    forecast = moving_average_forecast(historical, window=3, periods=periods)

    now = datetime.now()
    labels = [(now + timedelta(days=30 * i)).strftime('%B %Y') for i in range(1, periods + 1)]

    trend = 'increasing' if forecast[-1] > forecast[0] else (
        'decreasing' if forecast[-1] < forecast[0] else 'stable'
    )

    return {
        'crop_type': crop_type,
        'forecast_months': periods,
        'predicted_demand_kg': forecast,
        'month_labels': labels,
        'trend': trend,
        'historical_avg_kg': round(sum(historical) / len(historical), 2),
    }
