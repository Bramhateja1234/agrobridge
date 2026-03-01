"""AI Module: Crop Price Prediction using scikit-learn LinearRegression."""
import numpy as np
import os
import joblib
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder

# Mock training data: [crop_type_encoded, season_encoded, quantity_kg] -> price_per_kg
CROP_TYPES = ['grain', 'vegetable', 'fruit', 'pulse', 'oilseed', 'spice', 'other']
SEASONS = ['summer', 'winter', 'monsoon', 'spring']

TRAINING_DATA = [
    # [crop_type_enc, season_enc, quantity]  -> price
    [0, 0, 100],  # grain, summer, 100kg -> 25
    [0, 1, 200],  # grain, winter, 200kg -> 22
    [1, 0, 50],   # vegetable, summer -> 40
    [1, 2, 30],   # vegetable, monsoon -> 35
    [2, 0, 80],   # fruit, summer -> 80
    [2, 3, 60],   # fruit, spring -> 90
    [3, 1, 150],  # pulse, winter -> 55
    [3, 0, 100],  # pulse, summer -> 60
    [4, 1, 200],  # oilseed, winter -> 45
    [5, 3, 20],   # spice, spring -> 200
    [5, 0, 15],   # spice, summer -> 220
    [6, 2, 100],  # other, monsoon -> 30
]

TARGETS = [25, 22, 40, 35, 80, 90, 55, 60, 45, 200, 220, 30]

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'price_model.joblib')


def train_and_save():
    """Train the price prediction model and save to disk."""
    X = np.array(TRAINING_DATA)
    y = np.array(TARGETS)
    model = LinearRegression()
    model.fit(X, y)
    joblib.dump(model, MODEL_PATH)
    return model


def get_model():
    """Load or train the price model."""
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return train_and_save()


def predict_price(crop_type: str, season: str, quantity: float) -> float:
    """Predict price per kg for given crop type, season, and quantity."""
    model = get_model()
    crop_enc = CROP_TYPES.index(crop_type) if crop_type in CROP_TYPES else 6
    season_enc = SEASONS.index(season) if season in SEASONS else 0
    X = np.array([[crop_enc, season_enc, quantity]])
    price = model.predict(X)[0]
    return round(max(float(price), 1.0), 2)
