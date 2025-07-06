import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import re
import structlog

logger = structlog.get_logger()


class DataValidator:
    """Validator for market data integrity."""
    
    @staticmethod
    def validate_price_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate price data for consistency and quality."""
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ["open", "high", "low", "close"]
        for field in required_fields:
            if field not in data or data[field] is None:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        try:
            # Convert to Decimal for precise calculations
            open_price = Decimal(str(data["open"]))
            high_price = Decimal(str(data["high"]))
            low_price = Decimal(str(data["low"]))
            close_price = Decimal(str(data["close"]))
            
            # Basic price validation
            if any(price <= 0 for price in [open_price, high_price, low_price, close_price]):
                errors.append("All prices must be positive")
            
            # High/Low validation
            if high_price < low_price:
                errors.append("High price cannot be less than low price")
            
            # Open/Close within High/Low range
            if not (low_price <= open_price <= high_price):
                warnings.append("Open price outside high/low range")
            
            if not (low_price <= close_price <= high_price):
                warnings.append("Close price outside high/low range")
            
            # Volume validation
            if "volume" in data and data["volume"] is not None:
                try:
                    volume = int(data["volume"])
                    if volume < 0:
                        errors.append("Volume cannot be negative")
                except (ValueError, TypeError):
                    errors.append("Invalid volume format")
            
            # Price movement validation (warn for extreme movements)
            price_change = abs(close_price - open_price) / open_price
            if price_change > Decimal("0.5"):  # 50% change
                warnings.append(f"Large price movement detected: {price_change:.2%}")
            
        except (InvalidOperation, ValueError, TypeError) as e:
            errors.append(f"Invalid price format: {str(e)}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    @staticmethod
    def validate_symbol(symbol: str) -> Dict[str, Any]:
        """Validate asset symbol format."""
        errors = []
        warnings = []
        
        if not symbol:
            errors.append("Symbol cannot be empty")
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        # Basic symbol format validation
        symbol = symbol.upper().strip()
        
        # Length check
        if len(symbol) < 1 or len(symbol) > 20:
            errors.append("Symbol must be between 1 and 20 characters")
        
        # Character validation (alphanumeric, dots, hyphens)
        if not re.match(r'^[A-Z0-9.-]+$', symbol):
            errors.append("Symbol can only contain letters, numbers, dots, and hyphens")
        
        # Common symbol patterns
        if symbol.count('.') > 2:
            warnings.append("Symbol contains multiple dots - verify format")
        
        if symbol.count('-') > 1:
            warnings.append("Symbol contains multiple hyphens - verify format")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "normalized_symbol": symbol
        }
    
    @staticmethod
    def validate_date_range(start_date: Optional[datetime], end_date: Optional[datetime]) -> Dict[str, Any]:
        """Validate date range for data requests."""
        errors = []
        warnings = []
        
        if start_date and end_date:
            if start_date > end_date:
                errors.append("Start date cannot be after end date")
            
            # Check for reasonable date ranges
            range_days = (end_date - start_date).days
            if range_days > 3650:  # 10 years
                warnings.append("Date range is very large - this may impact performance")
            
            # Check if dates are in the future
            now = datetime.now()
            if start_date > now:
                warnings.append("Start date is in the future")
            if end_date > now:
                warnings.append("End date is in the future")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }


class RateLimiter:
    """Rate limiter for API calls."""
    
    def __init__(self, max_requests: int = 5, time_window: int = 1):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, List[datetime]] = {}
        self.lock = asyncio.Lock()
    
    async def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed under rate limit."""
        async with self.lock:
            now = datetime.now()
            
            # Initialize or clean old requests
            if identifier not in self.requests:
                self.requests[identifier] = []
            else:
                # Remove old requests outside the time window
                cutoff = now - timedelta(seconds=self.time_window)
                self.requests[identifier] = [
                    req_time for req_time in self.requests[identifier]
                    if req_time > cutoff
                ]
            
            # Check if under limit
            if len(self.requests[identifier]) < self.max_requests:
                self.requests[identifier].append(now)
                return True
            
            return False
    
    async def wait_time(self, identifier: str) -> float:
        """Get the time to wait before next request is allowed."""
        async with self.lock:
            if identifier not in self.requests or not self.requests[identifier]:
                return 0.0
            
            oldest_request = min(self.requests[identifier])
            time_since_oldest = (datetime.now() - oldest_request).total_seconds()
            
            if time_since_oldest >= self.time_window:
                return 0.0
            
            return self.time_window - time_since_oldest


class DataQualityChecker:
    """Check quality of fetched market data."""
    
    @staticmethod
    def check_data_completeness(data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check completeness of price data."""
        if not data:
            return {
                "score": 0.0,
                "issues": ["No data available"],
                "recommendations": ["Check symbol validity", "Try different time period"]
            }
        
        total_points = len(data)
        issues = []
        recommendations = []
        
        # Check for missing values
        missing_counts = {"open": 0, "high": 0, "low": 0, "close": 0, "volume": 0}
        
        for point in data:
            for field in missing_counts:
                if field not in point or point[field] is None:
                    missing_counts[field] += 1
        
        # Calculate completeness score
        critical_fields = ["open", "high", "low", "close"]
        critical_missing = sum(missing_counts[field] for field in critical_fields)
        critical_total = len(critical_fields) * total_points
        
        if critical_total > 0:
            completeness_score = 1 - (critical_missing / critical_total)
        else:
            completeness_score = 0.0
        
        # Generate issues and recommendations
        for field, missing in missing_counts.items():
            if missing > 0:
                percentage = (missing / total_points) * 100
                issues.append(f"{missing} missing {field} values ({percentage:.1f}%)")
                
                if field in critical_fields and percentage > 10:
                    recommendations.append(f"High missing rate for {field} - consider different data source")
        
        # Check for data gaps
        if total_points > 1:
            dates = []
            for point in data:
                if "date" in point:
                    try:
                        date = datetime.fromisoformat(point["date"].replace('Z', '+00:00'))
                        dates.append(date)
                    except:
                        pass
            
            if len(dates) > 1:
                dates.sort()
                gaps = []
                for i in range(1, len(dates)):
                    gap_days = (dates[i] - dates[i-1]).days
                    if gap_days > 7:  # More than a week gap
                        gaps.append(gap_days)
                
                if gaps:
                    issues.append(f"Found {len(gaps)} data gaps (largest: {max(gaps)} days)")
                    recommendations.append("Consider filling data gaps or using interpolation")
        
        return {
            "score": completeness_score,
            "issues": issues,
            "recommendations": recommendations,
            "metrics": {
                "total_points": total_points,
                "missing_counts": missing_counts,
                "completeness_score": completeness_score
            }
        }
    
    @staticmethod
    def detect_anomalies(data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect anomalies in price data."""
        if len(data) < 2:
            return {"anomalies": [], "score": 1.0}
        
        anomalies = []
        
        try:
            # Calculate price changes
            for i in range(1, len(data)):
                current = data[i]
                previous = data[i-1]
                
                if "close" in current and "close" in previous:
                    current_close = float(current["close"])
                    previous_close = float(previous["close"])
                    
                    if previous_close > 0:
                        change_percent = abs(current_close - previous_close) / previous_close
                        
                        # Flag large movements (>20% daily change)
                        if change_percent > 0.20:
                            anomalies.append({
                                "type": "large_price_movement",
                                "date": current.get("date"),
                                "change_percent": change_percent,
                                "description": f"Price change of {change_percent:.2%}"
                            })
                
                # Check for zero or negative prices
                for price_field in ["open", "high", "low", "close"]:
                    if price_field in current:
                        price = current[price_field]
                        if price is not None and float(price) <= 0:
                            anomalies.append({
                                "type": "invalid_price",
                                "date": current.get("date"),
                                "field": price_field,
                                "value": price,
                                "description": f"Invalid {price_field} price: {price}"
                            })
        
        except Exception as e:
            logger.warning("Error detecting anomalies", error=str(e))
        
        # Calculate quality score based on anomaly count
        anomaly_rate = len(anomalies) / len(data)
        quality_score = max(0.0, 1.0 - (anomaly_rate * 2))  # Penalize anomalies
        
        return {
            "anomalies": anomalies,
            "score": quality_score,
            "anomaly_rate": anomaly_rate
        }
