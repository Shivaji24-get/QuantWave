"""
Harmonic Pattern Detection Module
Detects Gartley, Butterfly, Bat, and Crab patterns using Fibonacci retracements.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from .mss_detector import SwingPoint, MSSDetector


@dataclass
class HarmonicPattern:
    """Represents a detected Harmonic Pattern"""
    name: str
    direction: str  # 'bullish' or 'bearish'
    points: Dict[str, SwingPoint]  # X, A, B, C, D
    ratios: Dict[str, float]  # AB/XA, BC/AB, CD/BC, AD/XA
    confidence: float
    timestamp: pd.Timestamp


class HarmonicDetector:
    """
    Detects Harmonic Patterns based on Fibonacci ratios:
    - Gartley
    - Butterfly
    - Bat
    - Crab
    """

    # Fibonacci Ratio Tolerances
    TOLERANCE = 0.15

    # Pattern Definitions (Ratios)
    PATTERNS = {
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

    def __init__(self, swing_lookback: int = 5):
        self.mss_detector = MSSDetector(swing_lookback=swing_lookback)
        
    def detect_patterns(self, df: pd.DataFrame) -> List[HarmonicPattern]:
        """
        Detect harmonic patterns in the given DataFrame.
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
        # Try different combinations of the last 10 swings
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
        """Validate if 5 points form a harmonic pattern."""
        X, A, B, C, D = points[0], points[1], points[2], points[3], points[4]
        
        # Calculate leg lengths
        XA = abs(A.price - X.price)
        AB = abs(B.price - A.price)
        BC = abs(C.price - B.price)
        CD = abs(D.price - C.price)
        AD = abs(D.price - A.price) # Actually it should be D relative to XA
        
        if XA == 0 or AB == 0 or BC == 0:
            return None
            
        # Ratios
        ab_xa = AB / XA
        bc_ab = BC / AB
        cd_bc = CD / BC
        ad_xa = abs(D.price - X.price) / XA # D retracement of XA

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
            if confidence > 0.7 and confidence > max_confidence:
                max_confidence = confidence
                best_pattern = name
                
        if best_pattern:
            return HarmonicPattern(
                name=best_pattern,
                direction=direction,
                points={'X': X, 'A': A, 'B': B, 'C': C, 'D': D},
                ratios=ratios,
                confidence=max_confidence,
                timestamp=D.timestamp
            )
            
        return None

    def _calculate_confidence(self, ratios: Dict[str, float], def_ratios: Dict[str, Any]) -> float:
        """Calculate confidence score based on ratio proximity."""
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

    def get_harmonic_analysis(self, df: pd.DataFrame) -> Dict:
        """Get comprehensive Harmonic analysis."""
        patterns = self.detect_patterns(df)
        
        if not patterns:
            return {'has_pattern': False, 'patterns': []}
            
        # Sort by most recent D point
        patterns.sort(key=lambda x: x.points['D'].index, reverse=True)
        
        latest = patterns[0]
        
        return {
            'has_pattern': True,
            'pattern_count': len(patterns),
            'latest_pattern': latest.name,
            'direction': latest.direction,
            'confidence': latest.confidence,
            'all_patterns': patterns
        }
