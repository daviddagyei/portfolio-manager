#!/usr/bin/env python3
"""
Quick test script for Portfolio Optimization endpoints.
Tests the basic functionality of optimization API endpoints.
"""

import requests
import json
import sys
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8080"
API_BASE = f"{BASE_URL}/api/v1"

def test_optimization_methods():
    """Test getting available optimization methods"""
    print("Testing optimization methods endpoint...")
    
    try:
        response = requests.get(f"{API_BASE}/optimization/methods")
        if response.status_code == 200:
            methods = response.json()
            print(f"✅ Available optimization methods: {methods}")
            return True
        else:
            print(f"❌ Failed to get optimization methods: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing optimization methods: {e}")
        return False

def test_efficient_frontier():
    """Test efficient frontier calculation"""
    print("\nTesting efficient frontier endpoint...")
    
    # Sample portfolio data
    test_data = {
        "portfolio_id": 1,
        "symbols": ["AAPL", "GOOGL", "MSFT"],
        "num_portfolios": 100
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/optimization/efficient-frontier",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Efficient frontier calculated with {len(result.get('portfolios', []))} portfolios")
            return True
        else:
            print(f"❌ Failed to calculate efficient frontier: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing efficient frontier: {e}")
        return False

def test_portfolio_optimization():
    """Test portfolio optimization"""
    print("\nTesting portfolio optimization endpoint...")
    
    # Sample optimization request
    test_data = {
        "portfolio_id": 1,
        "symbols": ["AAPL", "GOOGL", "MSFT"],
        "objective": "max_sharpe",
        "constraints": {
            "max_weight": 0.4,
            "min_weight": 0.05
        }
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/optimization/optimize",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Portfolio optimized with objective: {result.get('objective')}")
            print(f"   Expected return: {result.get('expected_return', 0):.4f}")
            print(f"   Risk (volatility): {result.get('volatility', 0):.4f}")
            return True
        else:
            print(f"❌ Failed to optimize portfolio: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing portfolio optimization: {e}")
        return False

def main():
    """Run all optimization tests"""
    print("🚀 Starting Portfolio Optimization API Tests\n")
    
    tests = [
        test_optimization_methods,
        test_efficient_frontier,
        test_portfolio_optimization
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All optimization tests passed!")
        return 0
    else:
        print("⚠️  Some optimization tests failed. Check the backend logs.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
