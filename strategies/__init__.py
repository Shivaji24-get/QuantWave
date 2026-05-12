"""
Trading strategy modules for QuantWave.
"""

from .base import Pattern, Signal, PatternDetector, SignalGenerator, Scanner
from .harmonic_detector import HarmonicDetector
from .harmonic_scanner import HarmonicScanner
from .mss_detector import MSSDetector
from .validators import DataValidator, PatternValidator, DuplicateValidator
from .risk_manager import RiskManager


class StockScanner(HarmonicScanner):
    """
    Wrapper for HarmonicScanner with backward-compatible parameter names.
    
    Accepts old parameter names and maps them to HarmonicScanner parameters.
    """
    
    def __init__(
        self,
        enable_patterns: bool = True,
        enable_scoring: bool = True,
        enable_smc: bool = False,
        **kwargs
    ):
        """
        Initialize StockScanner with backward-compatible parameters.
        
        Args:
            enable_patterns: Enable pattern detection (ignored, always enabled)
            enable_scoring: Enable signal scoring (ignored, always enabled)
            enable_smc: Enable SMC analysis (not supported, ignored)
            **kwargs: Additional arguments passed to HarmonicScanner
        """
        # Map old parameters to new ones if needed
        # For now, just pass through to HarmonicScanner
        super().__init__(**kwargs)


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
