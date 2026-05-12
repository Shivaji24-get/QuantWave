"""
Trading strategy modules for QuantWave.
"""

from .base import Pattern, Signal, PatternDetector, SignalGenerator, Scanner
from .harmonic_detector import HarmonicDetector
from .harmonic_scanner import HarmonicScanner
from .mss_detector import MSSDetector
from .validators import DataValidator, PatternValidator, DuplicateValidator
from .risk_manager import RiskManager

# Aliases for backward compatibility
StockScanner = HarmonicScanner

__all__ = [
    'Pattern',
    'Signal',
    'PatternDetector',
    'SignalGenerator',
    'Scanner',
    'HarmonicDetector',
    'HarmonicScanner',
    'MSSDetector',
    'DataValidator',
    'PatternValidator',
    'DuplicateValidator',
    'RiskManager',
    'StockScanner',
]
