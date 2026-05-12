"""
Trading strategy modules for QuantWave.
"""

from typing import Dict, List, Any
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
    
    def scan_all(self, client, symbols: List[str], timeframe: str = "D", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Backward-compatible method for scanning multiple symbols.
        
        Args:
            client: Fyers API client instance
            symbols: List of trading symbols
            timeframe: Timeframe for analysis
            limit: Number of candles to analyze
            
        Returns:
            List of scan results
        """
        results = self.scan_multiple(symbols, timeframe=timeframe, limit=limit, client=client)
        return results
    
    def scan_all_smc(self, client, symbols: List[str], ltf_timeframe: str = "5m", htf_timeframe: str = "D") -> List[Dict[str, Any]]:
        """
        Backward-compatible method for SMC scanning (not supported).
        
        Args:
            client: Fyers API client instance
            symbols: List of trading symbols
            ltf_timeframe: Lower timeframe
            htf_timeframe: Higher timeframe
            
        Returns:
            Empty list (SMC not supported in current implementation)
        """
        # SMC scanning not supported in current HarmonicScanner
        return []


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
