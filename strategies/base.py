"""
Base classes and interfaces for pattern detection strategies.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import pandas as pd


@dataclass
class Pattern:
    """Base class for detected patterns."""
    name: str = ""
    direction: str = ""  # 'bullish' or 'bearish'
    confidence: float = 0.0
    timestamp: Optional[pd.Timestamp] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_reward: Optional[float] = None


@dataclass
class Signal:
    """Represents a trading signal."""
    symbol: str
    action: str  # 'BUY', 'SELL', 'HOLD'
    score: float
    price: float
    pattern: Optional[str] = None
    pattern_confidence: Optional[float] = None
    timestamp: pd.Timestamp = None
    metadata: Dict[str, Any] = None


class PatternDetector(ABC):
    """Abstract base class for pattern detectors."""
    
    @abstractmethod
    def detect(self, df: pd.DataFrame) -> List[Pattern]:
        """
        Detect patterns in the given DataFrame.
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            List of detected patterns
        """
        pass
    
    @abstractmethod
    def get_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get comprehensive analysis of patterns in the data.
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            Dictionary with analysis results
        """
        pass


class SignalGenerator(ABC):
    """Abstract base class for signal generators."""
    
    @abstractmethod
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> Signal:
        """
        Generate a trading signal for the given symbol.
        
        Args:
            df: DataFrame with OHLC data
            symbol: Trading symbol
            
        Returns:
            Signal object
        """
        pass
    
    @abstractmethod
    def analyze(self, df: pd.DataFrame) -> str:
        """
        Analyze data and return signal action.
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            Signal action ('BUY', 'SELL', 'HOLD')
        """
        pass


class Scanner(ABC):
    """Abstract base class for market scanners."""
    
    @abstractmethod
    def scan_symbol(self, symbol: str, timeframe: str = "D", limit: int = 100) -> Dict[str, Any]:
        """
        Scan a single symbol for patterns/signals.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe for analysis
            limit: Number of candles to analyze
            
        Returns:
            Dictionary with scan results
        """
        pass
    
    @abstractmethod
    def scan_multiple(self, symbols: List[str], timeframe: str = "D", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Scan multiple symbols for patterns/signals.
        
        Args:
            symbols: List of trading symbols
            timeframe: Timeframe for analysis
            limit: Number of candles to analyze
            
        Returns:
            List of scan results
        """
        pass
