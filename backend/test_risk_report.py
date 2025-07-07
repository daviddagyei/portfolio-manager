#!/usr/bin/env python3
"""
Test script for Risk Analytics Report API
"""

import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Generate sample returns data (better performing portfolio)
np.random.seed(123)
dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')
returns = np.random.normal(0.0005, 0.015, len(dates))  # 0.05% daily return, 1.5% volatility

# Create sample data
sample_data = []
for i, date in enumerate(dates):
    sample_data.append({
        'date': date.strftime('%Y-%m-%d'),
        'return': returns[i]
    })

# Test report generation
test_request = {
    "returns_data": sample_data,
    "portfolio_name": "Test Portfolio",
    "risk_free_rate": 0.02,
    "rolling_window": 252
}

# Make API call
url = "http://127.0.0.1:8002/api/v1/risk-analytics/risk-report"
headers = {'Content-Type': 'application/json'}

print("Testing Risk Analytics Report API...")
print(f"URL: {url}")
print(f"Sample data points: {len(sample_data)}")

try:
    response = requests.post(url, json=test_request, headers=headers)
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("Success!")
        print(f"Portfolio: {result['data']['portfolio_name']}")
        print(f"Period: {result['data']['period']['start']} to {result['data']['period']['end']}")
        print(f"Data points: {result['data']['period']['data_points']}")
        print("\nExecutive Summary:")
        summary = result['data']['executive_summary']
        print(f"  Annual Return: {summary['annualized_return']:.4f}")
        print(f"  Volatility: {summary['volatility']:.4f}")
        print(f"  Sharpe Ratio: {summary['sharpe_ratio']:.4f}")
        print(f"  Max Drawdown: {summary['max_drawdown']:.4f}")
        print(f"  VaR (95%): {summary['var_95']:.4f}")
        print(f"\nRisk Assessment: {result['data']['risk_assessment']}")
        print(f"Recommendations: {len(result['data']['recommendations'])} items")
        for i, rec in enumerate(result['data']['recommendations'], 1):
            print(f"  {i}. {rec}")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Exception: {e}")
