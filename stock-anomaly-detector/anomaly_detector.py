import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose
from sklearn.ensemble import IsolationForest
from typing import Tuple, Optional

class AnomalyDetector:
    def __init__(self, window_size=20, threshold=3.0):
        self.window_size = window_size
        self.threshold = threshold
        self.models = {}  # To store trained models per stock

    def z_score_detection(self, prices: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Detect anomalies using moving Z-score method
        """
        anomalies = np.zeros_like(prices)
        means = np.zeros_like(prices)
        stds = np.zeros_like(prices)
        
        for i in range(self.window_size, len(prices)):
            window = prices[i-self.window_size:i]
            mean = np.mean(window)
            std = np.std(window)
            
            if std == 0:
                z_score = 0
            else:
                z_score = (prices[i] - mean) / std
                
            means[i] = mean
            stds[i] = std
            anomalies[i] = abs(z_score) > self.threshold
            
        return anomalies, means, stds

    def isolation_forest_detection(self, prices: np.ndarray) -> np.ndarray:
        """
        Detect anomalies using Isolation Forest
        """
        if len(prices) < self.window_size * 2:
            return np.zeros_like(prices)
            
        # Reshape for sklearn
        X = prices.reshape(-1, 1)
        
        # Train or retrieve model
        model_key = tuple(prices[:self.window_size])
        if model_key not in self.models:
            self.models[model_key] = IsolationForest(contamination=0.05)
            self.models[model_key].fit(X[:self.window_size])
            
        preds = self.models[model_key].predict(X)
        return (preds == -1).astype(int)

    def detect(self, data: pd.DataFrame, method: str = 'zscore') -> Optional[pd.DataFrame]:
        """
        Detect anomalies in stock data
        """
        if len(data) < self.window_size:
            return None
            
        prices = data['Close'].values
        timestamps = data.index
        
        if method == 'zscore':
            anomalies, means, stds = self.z_score_detection(prices)
        elif method == 'isolation':
            anomalies = self.isolation_forest_detection(prices)
            means = np.zeros_like(prices)
            stds = np.zeros_like(prices)
        else:
            raise ValueError(f"Unknown method: {method}")
            
        results = []
        for i in range(len(prices)):
            if anomalies[i]:
                results.append({
                    'Time': timestamps[i],
                    'Close': prices[i],
                    'Mean': means[i] if method == 'zscore' else np.nan,
                    'Std': stds[i] if method == 'zscore' else np.nan,
                    'Method': method,
                    'Anomaly': True
                })
                
        return pd.DataFrame(results)