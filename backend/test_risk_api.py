#!/usr/bin/env python3
"""
Test script for Risk Analytics API endpoints
"""

import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Generate sample returns data
np.random.seed(42)
dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')
returns = np.random.normal(0.001, 0.02, len(dates))  # 0.1% daily return, 2% volatility

# Create sample data
sample_data = []
for i, date in enumerate(dates):
    sample_data.append({
        'date': date.strftime('%Y-%m-%d'),
        'return': returns[i]
    })

# Test data
test_request = {
    "returns_data": sample_data,
    "risk_free_rate": 0.02,
    "rolling_window": 252,
    "var_confidence": 0.05,
    "include_benchmark": False,
    "include_correlation": False
}

# Make API call
url = "http://127.0.0.1:8002/api/v1/risk-analytics/comprehensive-analysis"
headers = {'Content-Type': 'application/json'}

print("Testing Risk Analytics API...")
print(f"URL: {url}")
print(f"Sample data points: {len(sample_data)}")

try:
    response = requests.post(url, json=test_request, headers=headers)
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("Success!")
        print(f"Sharpe Ratio: {result['data']['basic_metrics']['sharpe_ratio']:.4f}")
        print(f"Volatility: {result['data']['basic_metrics']['volatility']:.4f}")
        print(f"Max Drawdown: {result['data']['basic_metrics']['max_drawdown']:.4f}")
        print(f"VaR (95%): {result['data']['basic_metrics']['var_95']:.4f}")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Exception: {e}")
