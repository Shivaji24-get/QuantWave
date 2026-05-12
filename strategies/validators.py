"""
Validation utilities for harmonic pattern detection.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates data quality for pattern detection."""
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> Tuple[bool, Optional[str]]:
        """
        Validate DataFrame for pattern detection.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if df is None or df.empty:
            return False, "DataFrame is empty or None"
        
        required_columns = ['high', 'low', 'close']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, f"Missing required columns: {', '.join(missing_columns)}"
        
        if len(df) < 50:
            return False, f"Insufficient data: {len(df)} candles (need 50+)"
        
        # Check for NaN values
        if df[required_columns].isnull().any().any():
            return False, "DataFrame contains NaN values in required columns"
        
        # Check for zero or negative prices
        if (df['high'] <= 0).any() or (df['low'] <= 0).any() or (df['close'] <= 0).any():
            return False, "DataFrame contains zero or negative prices"
        
        # Check for invalid OHLC relationships
        invalid_ohlc = (df['high'] < df['low']) | (df['close'] > df['high']) | (df['close'] < df['low'])
        if invalid_ohlc.any():
            count = invalid_ohlc.sum()
            logger.warning(f"Found {count} candles with invalid OHLC relationships")
        
        return True, None
    
    @staticmethod
    def validate_symbol(symbol: str) -> Tuple[bool, Optional[str]]:
        """
        Validate symbol format.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not symbol or not isinstance(symbol, str):
            return False, "Symbol must be a non-empty string"
        
        if len(symbol) < 3:
            return False, "Symbol is too short"
        
        return True, None
    
    @staticmethod
    def validate_timeframe(timeframe: str) -> Tuple[bool, Optional[str]]:
        """
        Validate timeframe format.
        
        Args:
            timeframe: Timeframe string (e.g., "D", "5m", "15m", "1h")
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        valid_timeframes = ['1m', '3m', '5m', '10m', '15m', '30m', '60m', '1h', '2h', '3h', '4h', 'D', 'W', 'M']
        
        if not timeframe or not isinstance(timeframe, str):
            return False, "Timeframe must be a non-empty string"
        
        if timeframe not in valid_timeframes:
            return False, f"Invalid timeframe. Valid options: {', '.join(valid_timeframes)}"
        
        return True, None


class PatternValidator:
    """Validates harmonic pattern properties."""
    
    @staticmethod
    def validate_ratios(ratios: Dict[str, float]) -> Tuple[bool, Optional[str]]:
        """
        Validate Fibonacci ratios.
        
        Args:
            ratios: Dictionary of Fibonacci ratios
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        required_ratios = ['AB_XA', 'BC_AB', 'CD_BC', 'AD_XA']
        
        for ratio in required_ratios:
            if ratio not in ratios:
                return False, f"Missing required ratio: {ratio}"
            
            if not isinstance(ratios[ratio], (int, float)):
                return False, f"Ratio {ratio} must be a number"
            
            if ratios[ratio] <= 0:
                return False, f"Ratio {ratio} must be positive"
        
        # Check for reasonable ratio ranges
        if ratios['AB_XA'] > 2.0:
            logger.warning(f"AB_XA ratio {ratios['AB_XA']:.2f} is unusually high")
        
        if ratios['CD_BC'] > 5.0:
            logger.warning(f"CD_BC ratio {ratios['CD_BC']:.2f} is unusually high")
        
        return True, None
    
    @staticmethod
    def validate_confidence(confidence: float, min_threshold: float = 0.5) -> Tuple[bool, Optional[str]]:
        """
        Validate pattern confidence score.
        
        Args:
            confidence: Confidence score (0-1)
            min_threshold: Minimum acceptable confidence
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(confidence, (int, float)):
            return False, "Confidence must be a number"
        
        if confidence < 0 or confidence > 1:
            return False, "Confidence must be between 0 and 1"
        
        if confidence < min_threshold:
            return False, f"Confidence {confidence:.2f} below threshold {min_threshold}"
        
        return True, None
    
    @staticmethod
    def validate_risk_reward(risk_reward: float, min_rr: float = 1.5) -> Tuple[bool, Optional[str]]:
        """
        Validate risk/reward ratio.
        
        Args:
            risk_reward: Risk/reward ratio
            min_rr: Minimum acceptable risk/reward
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(risk_reward, (int, float)):
            return False, "Risk/reward must be a number"
        
        if risk_reward <= 0:
            return False, "Risk/reward must be positive"
        
        if risk_reward < min_rr:
            logger.warning(f"Risk/reward {risk_reward:.2f} below recommended minimum {min_rr}")
        
        return True, None


class APIValidator:
    """Validates API responses and rate limits."""
    
    def __init__(self, max_requests_per_minute: int = 60):
        """
        Initialize API Validator.
        
        Args:
            max_requests_per_minute: Maximum API requests per minute
        """
        self.max_requests_per_minute = max_requests_per_minute
        self.request_timestamps: List[float] = []
    
    def check_rate_limit(self) -> Tuple[bool, Optional[str]]:
        """
        Check if API rate limit would be exceeded.
        
        Returns:
            Tuple of (can_proceed, error_message)
        """
        import time
        
        current_time = time.time()
        
        # Remove timestamps older than 1 minute
        self.request_timestamps = [
            ts for ts in self.request_timestamps
            if current_time - ts < 60
        ]
        
        if len(self.request_timestamps) >= self.max_requests_per_minute:
            return False, f"Rate limit exceeded: {len(self.request_timestamps)} requests in last minute"
        
        return True, None
    
    def record_request(self):
        """Record an API request timestamp."""
        import time
        self.request_timestamps.append(time.time())
    
    def validate_response(self, response: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate API response.
        
        Args:
            response: API response dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(response, dict):
            return False, "Response must be a dictionary"
        
        if 'error' in response:
            return False, f"API returned error: {response['error']}"
        
        return True, None


class DuplicateValidator:
    """Validates and filters duplicate patterns."""
    
    def __init__(self, time_window_minutes: int = 30):
        """
        Initialize Duplicate Validator.
        
        Args:
            time_window_minutes: Time window to consider patterns as duplicates
        """
        self.time_window_minutes = time_window_minutes
        self._seen_patterns: Dict[str, float] = {}  # pattern_key -> timestamp
    
    def is_duplicate(self, pattern: Dict[str, Any]) -> bool:
        """
        Check if pattern is a duplicate of a recently seen pattern.
        
        Args:
            pattern: Pattern dictionary
            
        Returns:
            True if duplicate, False otherwise
        """
        import time
        
        # Create pattern key
        key = f"{pattern['symbol']}_{pattern['name']}_{pattern['direction']}"
        
        current_time = time.time()
        
        # Check if seen within time window
        if key in self._seen_patterns:
            last_seen = self._seen_patterns[key]
            time_diff = (current_time - last_seen) / 60  # Convert to minutes
            
            if time_diff < self.time_window_minutes:
                return True
        
        # Record this pattern
        self._seen_patterns[key] = current_time
        
        return False
    
    def cleanup_old_patterns(self):
        """Remove old pattern records."""
        import time
        
        current_time = time.time()
        cutoff_time = current_time - (self.time_window_minutes * 60)
        
        self._seen_patterns = {
            key: ts for key, ts in self._seen_patterns.items()
            if ts > cutoff_time
        }
