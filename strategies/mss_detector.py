"""
Market Structure Shift (MSS) Detector Module
Identifies swing highs and lows in price action for harmonic pattern detection.
"""
import pandas as pd
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class SwingPoint:
    """Represents a swing high or low point."""
    index: int
    price: float
    timestamp: pd.Timestamp
    type: str  # 'high' or 'low'


class MSSDetector:
    """
    Detects Market Structure Shifts by identifying swing highs and lows.
    
    Uses a lookback period to identify local extremum points that represent
    changes in market structure.
    """
    
    def __init__(self, swing_lookback: int = 5):
        """
        Initialize MSS Detector.
        
        Args:
            swing_lookback: Number of bars on each side to identify a swing point
        """
        self.swing_lookback = swing_lookback
    
    def find_swings(self, df: pd.DataFrame) -> Tuple[List[SwingPoint], List[SwingPoint]]:
        """
        Identify swing highs and lows in the price data.
        
        Args:
            df: DataFrame with OHLC data (must have 'high', 'low', 'timestamp' columns)
            
        Returns:
            Tuple of (swing_highs, swing_lows) lists
        """
        if df.empty or len(df) < self.swing_lookback * 2 + 1:
            return [], []
        
        highs = []
        lows = []
        
        high_prices = df['high'].values
        low_prices = df['low'].values
        timestamps = df['timestamp'].values if 'timestamp' in df.columns else df.index
        
        lookback = self.swing_lookback
        
        for i in range(lookback, len(df) - lookback):
            # Check for swing high
            is_swing_high = True
            for j in range(i - lookback, i + lookback + 1):
                if j != i and high_prices[j] >= high_prices[i]:
                    is_swing_high = False
                    break
            
            if is_swing_high:
                highs.append(SwingPoint(
                    index=i,
                    price=high_prices[i],
                    timestamp=timestamps[i] if isinstance(timestamps[i], pd.Timestamp) else pd.Timestamp(timestamps[i]),
                    type='high'
                ))
            
            # Check for swing low
            is_swing_low = True
            for j in range(i - lookback, i + lookback + 1):
                if j != i and low_prices[j] <= low_prices[i]:
                    is_swing_low = False
                    break
            
            if is_swing_low:
                lows.append(SwingPoint(
                    index=i,
                    price=low_prices[i],
                    timestamp=timestamps[i] if isinstance(timestamps[i], pd.Timestamp) else pd.Timestamp(timestamps[i]),
                    type='low'
                ))
        
        return highs, lows
    
    def get_recent_structure(self, df: pd.DataFrame, num_points: int = 10) -> List[SwingPoint]:
        """
        Get the most recent swing points combined.
        
        Args:
            df: DataFrame with OHLC data
            num_points: Number of recent swing points to return
            
        Returns:
            List of recent swing points sorted by index
        """
        highs, lows = self.find_swings(df)
        all_swings = sorted(highs + lows, key=lambda x: x.index)
        return all_swings[-num_points:] if len(all_swings) >= num_points else all_swings
