"""
Harmonic Pattern Detection Module
Detects Gartley, Butterfly, Bat, and Crab patterns using Fibonacci retracements.

This module provides pattern detection based on Fibonacci ratio validation
for identifying potential reversal zones in price action.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from .mss_detector import SwingPoint, MSSDetector
from .base import Pattern, PatternDetector


@dataclass
class HarmonicPattern(Pattern):
    """Represents a detected Harmonic Pattern with specific Fibonacci ratios."""
    points: Dict[str, SwingPoint] = None  # X, A, B, C, D
    ratios: Dict[str, float] = None  # AB/XA, BC/AB, CD/BC, AD/XA
    prz: Optional[Dict[str, float]] = None  # Potential Reversal Zone


class HarmonicDetector(PatternDetector):
    """
    Detects Harmonic Patterns based on Fibonacci ratios:
    - Gartley
    - Butterfly
    - Bat
    - Crab
    
    This detector identifies XABCD patterns by validating Fibonacci
    retracement ratios between swing points.
    """

    # Fibonacci Ratio Tolerances
    TOLERANCE = 0.15

    # Pattern Definitions (Ratios)
    PATTERNS: Dict[str, Dict[str, Union[float, Tuple[float, float]]]] = {
        'Gartley': {
            'AB_XA': 0.618,
            'BC_AB': (0.382, 0.886),
            'CD_BC': (1.272, 1.618),
            'AD_XA': 0.786
        },
        'Butterfly': {
            'AB_XA': 0.786,
            'BC_AB': (0.382, 0.886),
            'CD_BC': (1.618, 2.618),
            'AD_XA': (1.27, 1.618)
        },
        'Bat': {
            'AB_XA': (0.382, 0.50),
            'BC_AB': (0.382, 0.886),
            'CD_BC': (1.618, 2.618),
            'AD_XA': 0.886
        },
        'Crab': {
            'AB_XA': (0.382, 0.618),
            'BC_AB': (0.382, 0.886),
            'CD_BC': (2.24, 3.618),
            'AD_XA': 1.618
        }
    }

    def __init__(self, swing_lookback: int = 5, min_confidence: float = 0.7):
        """
        Initialize Harmonic Detector.
        
        Args:
            swing_lookback: Number of bars to identify swing points
            min_confidence: Minimum confidence threshold for pattern detection
        """
        self.mss_detector = MSSDetector(swing_lookback=swing_lookback)
        self.min_confidence = min_confidence
        
    def detect(self, df: pd.DataFrame) -> List[HarmonicPattern]:
        """
        Detect harmonic patterns in the given DataFrame.
        
        Args:
            df: DataFrame with OHLC data (must have 'high', 'low', 'timestamp' columns)
            
        Returns:
            List of detected HarmonicPattern objects
        """
        if df.empty or len(df) < 50:
            return []

        # Find swing points
        highs, lows = self.mss_detector.find_swings(df)
        
        # Combine and sort swings by index
        all_swings = sorted(highs + lows, key=lambda x: x.index)
        
        if len(all_swings) < 5:
            return []

        patterns = []
        
        # We need 5 points for XABCD (4 legs)
        # Try different combinations of the last 12 swings
        recent_swings = all_swings[-12:]
        
        for i in range(len(recent_swings) - 4):
            points_subset = recent_swings[i:i+5]
            
            # Check for Bullish XABCD (M-shape: X low, A high, B low, C high, D low)
            if (points_subset[0].type == 'low' and points_subset[1].type == 'high' and
                points_subset[2].type == 'low' and points_subset[3].type == 'high' and
                points_subset[4].type == 'low'):
                
                pattern = self._validate_pattern(points_subset, 'bullish')
                if pattern:
                    patterns.append(pattern)
            
            # Check for Bearish XABCD (W-shape: X high, A low, B high, C low, D high)
            elif (points_subset[0].type == 'high' and points_subset[1].type == 'low' and
                  points_subset[2].type == 'high' and points_subset[3].type == 'low' and
                  points_subset[4].type == 'high'):
                
                pattern = self._validate_pattern(points_subset, 'bearish')
                if pattern:
                    patterns.append(pattern)

        return patterns

    def _validate_pattern(self, points: List[SwingPoint], direction: str) -> Optional[HarmonicPattern]:
        """
        Validate if 5 points form a harmonic pattern.
        
        Args:
            points: List of 5 swing points (X, A, B, C, D)
            direction: 'bullish' or 'bearish'
            
        Returns:
            HarmonicPattern if valid, None otherwise
        """
        X, A, B, C, D = points[0], points[1], points[2], points[3], points[4]
        
        # Calculate leg lengths
        XA = abs(A.price - X.price)
        AB = abs(B.price - A.price)
        BC = abs(C.price - B.price)
        CD = abs(D.price - C.price)
        
        if XA == 0 or AB == 0 or BC == 0:
            return None
            
        # Ratios
        ab_xa = AB / XA
        bc_ab = BC / AB
        cd_bc = CD / BC
        ad_xa = abs(D.price - X.price) / XA  # D retracement of XA

        ratios = {
            'AB_XA': ab_xa,
            'BC_AB': bc_ab,
            'CD_BC': cd_bc,
            'AD_XA': ad_xa
        }
        
        best_pattern = None
        max_confidence = 0
        
        for name, def_ratios in self.PATTERNS.items():
            confidence = self._calculate_confidence(ratios, def_ratios)
            if confidence > self.min_confidence and confidence > max_confidence:
                max_confidence = confidence
                best_pattern = name
                
        if best_pattern:
            # Calculate Potential Reversal Zone (PRZ)
            prz = self._calculate_prz(D.price, direction, ratios)
            
            return HarmonicPattern(
                name=best_pattern,
                direction=direction,
                points={'X': X, 'A': A, 'B': B, 'C': C, 'D': D},
                ratios=ratios,
                confidence=max_confidence,
                timestamp=D.timestamp,
                entry_price=D.price,
                stop_loss=prz.get('stop_loss'),
                take_profit=prz.get('take_profit'),
                risk_reward=prz.get('risk_reward'),
                prz=prz
            )
            
        return None
    
    def _calculate_prz(self, d_price: float, direction: str, ratios: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate Potential Reversal Zone (PRZ) for the pattern.
        
        Args:
            d_price: Price at point D
            direction: 'bullish' or 'bearish'
            ratios: Fibonacci ratios from pattern validation
            
        Returns:
            Dictionary with stop_loss, take_profit, and risk_reward
        """
        # Default PRZ calculation based on pattern direction
        if direction == 'bullish':
            stop_loss = d_price * 0.99  # 1% below D
            take_profit = d_price * 1.02  # 2% above D
        else:
            stop_loss = d_price * 1.01  # 1% above D
            take_profit = d_price * 0.98  # 2% below D
        
        risk_reward = abs(take_profit - d_price) / abs(d_price - stop_loss)
        
        return {
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_reward': risk_reward
        }

    def _calculate_confidence(self, ratios: Dict[str, float], def_ratios: Dict[str, Any]) -> float:
        """
        Calculate confidence score based on ratio proximity.
        
        Args:
            ratios: Calculated Fibonacci ratios
            def_ratios: Expected ratio definitions (can be single value or tuple range)
            
        Returns:
            Confidence score between 0 and 1
        """
        scores = []
        
        for key, target in def_ratios.items():
            val = ratios[key]
            if isinstance(target, tuple):
                # Target is a range (min, max)
                if target[0] <= val <= target[1]:
                    scores.append(1.0)
                else:
                    # Partial score based on distance to range
                    dist = min(abs(val - target[0]), abs(val - target[1]))
                    proximity = max(0, 1 - (dist / (target[0] * self.TOLERANCE)))
                    scores.append(proximity)
            else:
                # Target is a single value
                proximity = max(0, 1 - (abs(val - target) / (target * self.TOLERANCE)))
                scores.append(proximity)
                
        return sum(scores) / len(scores)

    def get_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get comprehensive Harmonic analysis.
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            Dictionary with analysis results including patterns, confidence, etc.
        """
        patterns = self.detect(df)
        
        if not patterns:
            return {
                'has_pattern': False,
                'patterns': [],
                'pattern_count': 0
            }
            
        # Sort by most recent D point
        patterns.sort(key=lambda x: x.points['D'].index, reverse=True)
        
        latest = patterns[0]
        
        return {
            'has_pattern': True,
            'pattern_count': len(patterns),
            'latest_pattern': latest.name,
            'direction': latest.direction,
            'confidence': latest.confidence,
            'entry_price': latest.entry_price,
            'stop_loss': latest.stop_loss,
            'take_profit': latest.take_profit,
            'risk_reward': latest.risk_reward,
            'all_patterns': patterns
        }
    
    def get_harmonic_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Legacy method for backward compatibility.
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            Dictionary with analysis results
        """
        return self.get_analysis(df)
