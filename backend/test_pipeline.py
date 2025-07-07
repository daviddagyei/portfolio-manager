#!/usr/bin/env python3
"""
Comprehensive test script for the Risk Analytics Pipeline
Tests the complete flow from data generation to API responses
"""

import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys

BASE_URL = "http://127.0.0.1:8002/api/v1"

def generate_sample_portfolio_data():
    """Generate realistic sample portfolio data"""
    print("📊 Generating sample portfolio data...")
    
    # Generate 2 years of daily data
    np.random.seed(42)
    dates = pd.date_range(start='2022-01-01', end='2024-01-01', freq='D')
    
    # Create realistic portfolio returns with some trend
    base_return = 0.0008  # ~20% annual return
    volatility = 0.015    # ~23% annual volatility
    
    returns = []
    cumulative = 1.0
    
    for i, date in enumerate(dates):
        # Add some market cycles
        market_factor = 1 + 0.3 * np.sin(i / 252 * 2 * np.pi)  # Annual cycle
        daily_return = np.random.normal(base_return * market_factor, volatility)
        returns.append(daily_return)
        cumulative *= (1 + daily_return)
    
    # Create benchmark data (slightly lower returns, less volatility)
    benchmark_returns = []
    for i in range(len(dates)):
        market_factor = 1 + 0.2 * np.sin(i / 252 * 2 * np.pi)
        benchmark_return = np.random.normal(base_return * 0.8 * market_factor, volatility * 0.8)
        benchmark_returns.append(benchmark_return)
    
    return dates, returns, benchmark_returns

def test_comprehensive_analysis():
    """Test the comprehensive risk analysis endpoint"""
    print("\n🔍 Testing Comprehensive Risk Analysis...")
    
    dates, returns, benchmark_returns = generate_sample_portfolio_data()
    
    # Prepare data for API
    portfolio_data = []
    benchmark_data = []
    
    for i, date in enumerate(dates):
        portfolio_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'return': returns[i]
        })
        benchmark_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'return': benchmark_returns[i]
        })
    
    # Test request
    test_request = {
        "returns_data": portfolio_data,
        "benchmark_data": benchmark_data,
        "risk_free_rate": 0.02,
        "rolling_window": 252,
        "var_confidence": 0.05,
        "include_benchmark": True,
        "include_correlation": False
    }
    
    url = f"{BASE_URL}/risk-analytics/comprehensive-analysis"
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, json=test_request, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                data = result['data']
                basic_metrics = data['basic_metrics']
                
                print("   ✅ Success! Key metrics:")
                print(f"      Sharpe Ratio: {basic_metrics['sharpe_ratio']:.4f}")
                print(f"      Volatility: {basic_metrics['volatility']:.4f}")
                print(f"      Max Drawdown: {basic_metrics['max_drawdown']:.4f}")
                print(f"      VaR (95%): {basic_metrics['var_95']:.4f}")
                print(f"      Beta: {basic_metrics.get('beta', 'N/A')}")
                print(f"      Alpha: {basic_metrics.get('alpha', 'N/A')}")
                print(f"      Data Points: {data['data_points']}")
                
                # Check benchmark comparison
                if data.get('benchmark_comparison'):
                    bench = data['benchmark_comparison']
                    print(f"      Tracking Error: {bench['tracking_error']:.4f}")
                    print(f"      Information Ratio: {bench['information_ratio']:.4f}")
                
                return True
            else:
                print(f"   ❌ API returned success=False")
                return False
        else:
            print(f"   ❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

def test_risk_report():
    """Test the risk report endpoint"""
    print("\n📋 Testing Risk Report Generation...")
    
    dates, returns, _ = generate_sample_portfolio_data()
    
    # Prepare data for API
    portfolio_data = []
    for i, date in enumerate(dates):
        portfolio_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'return': returns[i]
        })
    
    test_request = {
        "returns_data": portfolio_data,
        "portfolio_name": "Test Portfolio",
        "risk_free_rate": 0.02,
        "rolling_window": 252
    }
    
    url = f"{BASE_URL}/risk-analytics/risk-report"
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, json=test_request, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                report = result['data']
                
                print("   ✅ Success! Report generated:")
                print(f"      Portfolio: {report['portfolio_name']}")
                print(f"      Period: {report['period']['start']} to {report['period']['end']}")
                print(f"      Risk Assessment: {report['risk_assessment']}")
                print(f"      Recommendations: {len(report['recommendations'])} items")
                
                for i, rec in enumerate(report['recommendations'][:3], 1):
                    print(f"        {i}. {rec}")
                
                return True
            else:
                print(f"   ❌ API returned success=False")
                return False
        else:
            print(f"   ❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

def test_frontend_service_compatibility():
    """Test that the API responses match frontend service expectations"""
    print("\n🔄 Testing Frontend Service Compatibility...")
    
    dates, returns, benchmark_returns = generate_sample_portfolio_data()
    
    # Test the exact format the frontend service expects
    portfolio_data = []
    for i, date in enumerate(dates):
        portfolio_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'return': returns[i]
        })
    
    test_request = {
        "returns_data": portfolio_data,
        "risk_free_rate": 0.02,
        "rolling_window": 252,
        "var_confidence": 0.05,
        "include_benchmark": False,
        "include_correlation": False
    }
    
    # Test comprehensive analysis
    url = f"{BASE_URL}/risk-analytics/comprehensive-analysis"
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, json=test_request, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if response structure matches frontend expectations
            required_fields = [
                'success', 'data'
            ]
            
            for field in required_fields:
                if field not in result:
                    print(f"   ❌ Missing field: {field}")
                    return False
            
            if result['success'] and result['data']:
                data = result['data']
                
                # Check data structure
                required_data_fields = [
                    'basic_metrics', 'performance_metrics', 'rolling_metrics', 
                    'var_metrics', 'calculation_date', 'period_start', 
                    'period_end', 'data_points'
                ]
                
                for field in required_data_fields:
                    if field not in data:
                        print(f"   ❌ Missing data field: {field}")
                        return False
                
                # Check basic_metrics structure
                basic_metrics = data['basic_metrics']
                required_basic_fields = [
                    'sharpe_ratio', 'volatility', 'max_drawdown', 
                    'var_95', 'cvar_95', 'calmar_ratio', 'sortino_ratio'
                ]
                
                for field in required_basic_fields:
                    if field not in basic_metrics:
                        print(f"   ❌ Missing basic_metrics field: {field}")
                        return False
                
                print("   ✅ Response structure matches frontend expectations!")
                return True
            else:
                print(f"   ❌ Invalid response structure")
                return False
        else:
            print(f"   ❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

def test_error_handling():
    """Test error handling with invalid data"""
    print("\n⚠️  Testing Error Handling...")
    
    # Test with insufficient data
    insufficient_data = [
        {'date': '2024-01-01', 'return': 0.01},
        {'date': '2024-01-02', 'return': -0.005}
    ]
    
    test_request = {
        "returns_data": insufficient_data,
        "risk_free_rate": 0.02,
        "rolling_window": 252
    }
    
    url = f"{BASE_URL}/risk-analytics/comprehensive-analysis"
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, json=test_request, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print("   ✅ Correctly handled insufficient data with error response")
            return True
        else:
            result = response.json()
            if not result.get('success'):
                print("   ✅ Correctly returned success=False for insufficient data")
                return True
            else:
                print("   ⚠️  Should have failed with insufficient data")
                return False
                
    except Exception as e:
        print(f"   ⚠️  Exception during error test: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Risk Analytics Pipeline Testing")
    print("=" * 60)
    
    tests = [
        ("Health Check", lambda: requests.get(f"{BASE_URL}/risk-analytics/health").status_code == 200),
        ("Comprehensive Analysis", test_comprehensive_analysis),
        ("Risk Report", test_risk_report),
        ("Frontend Compatibility", test_frontend_service_compatibility),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"   ✅ PASSED")
            else:
                print(f"   ❌ FAILED")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! The pipeline is working perfectly!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
