"""
Harmonic Pattern Scanner Module
Provides scanning functionality for harmonic patterns across multiple symbols and timeframes.
"""
import asyncio
import pandas as pd
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import time

from .harmonic_detector import HarmonicDetector, HarmonicPattern
from .base import Scanner, Signal
from .validators import DataValidator, PatternValidator, DuplicateValidator
from api import get_historical_data


logger = logging.getLogger(__name__)


class HarmonicScanner(Scanner):
    """
    Scanner for detecting harmonic patterns across multiple symbols.
    
    Supports:
    - Single symbol scanning
    - Multiple symbol scanning with parallel execution
    - Historical backtesting
    - Live continuous scanning
    - Multi-timeframe analysis
    - Data caching for performance
    - Duplicate pattern filtering
    """
    
    def __init__(
        self,
        detector: Optional[HarmonicDetector] = None,
        swing_lookback: int = 5,
        min_confidence: float = 0.7,
        max_workers: int = 4,
        cache_ttl: int = 60,
        enable_cache: bool = True,
        enable_duplicate_filter: bool = True
    ):
        """
        Initialize Harmonic Scanner.
        
        Args:
            detector: HarmonicDetector instance (created if None)
            swing_lookback: Lookback period for swing detection
            min_confidence: Minimum confidence threshold
            max_workers: Maximum parallel workers for scanning
            cache_ttl: Cache time-to-live in seconds
            enable_cache: Enable data caching
            enable_duplicate_filter: Enable duplicate pattern filtering
        """
        self.detector = detector or HarmonicDetector(
            swing_lookback=swing_lookback,
            min_confidence=min_confidence
        )
        self.max_workers = max_workers
        self.min_confidence = min_confidence
        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl
        
        # Data cache: key -> (data, timestamp)
        self._data_cache: Dict[str, tuple[pd.DataFrame, float]] = {}
        
        # Pattern cache: key -> (patterns, timestamp)
        self._pattern_cache: Dict[str, tuple[List[Dict[str, Any]], float]] = {}
        
        # Validators
        self.data_validator = DataValidator()
        self.pattern_validator = PatternValidator()
        self.duplicate_filter = DuplicateValidator() if enable_duplicate_filter else None
    
    def scan_symbol(
        self,
        symbol: str,
        timeframe: str = "D",
        limit: int = 100,
        client: Any = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Scan a single symbol for harmonic patterns.
        
        Args:
            symbol: Trading symbol (e.g., "NSE:RELIANCE-EQ")
            timeframe: Timeframe for analysis (D, 5m, 15m, etc.)
            limit: Number of candles to analyze
            client: Fyers API client instance
            use_cache: Use cached data if available
            
        Returns:
            Dictionary with scan results
        """
        try:
            # Validate inputs
            is_valid, error = self.data_validator.validate_symbol(symbol)
            if not is_valid:
                return {
                    'symbol': symbol,
                    'success': False,
                    'error': error,
                    'patterns': []
                }
            
            is_valid, error = self.data_validator.validate_timeframe(timeframe)
            if not is_valid:
                return {
                    'symbol': symbol,
                    'success': False,
                    'error': error,
                    'patterns': []
                }
            
            if client is None:
                return {
                    'symbol': symbol,
                    'success': False,
                    'error': 'API client not provided',
                    'patterns': []
                }
            
            # Check cache
            cache_key = f"{symbol}_{timeframe}_{limit}"
            if use_cache and self.enable_cache:
                cached_patterns, cache_time = self._pattern_cache.get(cache_key, (None, 0))
                if cached_patterns and (time.time() - cache_time) < self.cache_ttl:
                    logger.debug(f"Using cached patterns for {cache_key}")
                    return {
                        'symbol': symbol,
                        'success': True,
                        'timeframe': timeframe,
                        'current_price': cached_patterns[0].get('current_price') if cached_patterns else None,
                        'pattern_count': len(cached_patterns),
                        'patterns': cached_patterns,
                        'has_pattern': len(cached_patterns) > 0,
                        'cached': True
                    }
            
            # Fetch historical data with caching
            df = self._get_cached_data(symbol, timeframe, limit, client, use_cache)
            
            if df.empty:
                return {
                    'symbol': symbol,
                    'success': False,
                    'error': 'No data available',
                    'patterns': []
                }
            
            # Validate data
            is_valid, error = self.data_validator.validate_dataframe(df)
            if not is_valid:
                return {
                    'symbol': symbol,
                    'success': False,
                    'error': error,
                    'patterns': []
                }
            
            # Detect patterns
            patterns = self.detector.detect(df)
            
            # Convert patterns to serializable format and validate
            pattern_list = []
            for pattern in patterns:
                pattern_dict = {
                    'name': pattern.name,
                    'direction': pattern.direction,
                    'confidence': pattern.confidence,
                    'timestamp': pattern.timestamp.isoformat() if pattern.timestamp else None,
                    'entry_price': pattern.entry_price,
                    'stop_loss': pattern.stop_loss,
                    'take_profit': pattern.take_profit,
                    'risk_reward': pattern.risk_reward,
                    'ratios': pattern.ratios
                }
                
                # Validate ratios
                is_valid, _ = self.pattern_validator.validate_ratios(pattern.ratios)
                if is_valid:
                    # Check for duplicates
                    if self.duplicate_filter and self.duplicate_filter.is_duplicate(pattern_dict):
                        logger.debug(f"Filtered duplicate pattern for {symbol}")
                        continue
                    pattern_list.append(pattern_dict)
            
            # Get current price
            current_price = df['close'].iloc[-1] if not df.empty else None
            
            # Add current price to patterns
            for p in pattern_list:
                p['current_price'] = current_price
            
            # Cache results
            if self.enable_cache:
                self._pattern_cache[cache_key] = (pattern_list, time.time())
            
            return {
                'symbol': symbol,
                'success': True,
                'timeframe': timeframe,
                'current_price': current_price,
                'pattern_count': len(pattern_list),
                'patterns': pattern_list,
                'has_pattern': len(pattern_list) > 0,
                'cached': False
            }
            
        except Exception as e:
            logger.error(f"Error scanning {symbol}: {e}", exc_info=True)
            return {
                'symbol': symbol,
                'success': False,
                'error': str(e),
                'patterns': []
            }
    
    def _get_cached_data(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
        client: Any,
        use_cache: bool
    ) -> pd.DataFrame:
        """
        Get data from cache or fetch from API.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe for analysis
            limit: Number of candles to fetch
            client: Fyers API client instance
            use_cache: Use cached data if available
            
        Returns:
            DataFrame with OHLC data
        """
        cache_key = f"{symbol}_{timeframe}_{limit}"
        
        if use_cache and self.enable_cache:
            cached_data, cache_time = self._data_cache.get(cache_key, (None, 0))
            if cached_data is not None and (time.time() - cache_time) < self.cache_ttl:
                logger.debug(f"Using cached data for {cache_key}")
                return cached_data
        
        # Fetch from API
        df = get_historical_data(client, symbol, timeframe, count=limit)
        
        # Cache the data
        if self.enable_cache and not df.empty:
            self._data_cache[cache_key] = (df, time.time())
        
        return df
    
    def scan_multiple(
        self,
        symbols: List[str],
        timeframe: str = "D",
        limit: int = 100,
        client: Any = None,
        parallel: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Scan multiple symbols for harmonic patterns.
        
        Args:
            symbols: List of trading symbols
            timeframe: Timeframe for analysis
            limit: Number of candles to analyze
            client: Fyers API client instance
            parallel: Use parallel execution for faster scanning
            
        Returns:
            List of scan results
        """
        if not parallel or len(symbols) <= 1:
            # Sequential scanning
            results = []
            for symbol in symbols:
                result = self.scan_symbol(symbol, timeframe, limit, client)
                results.append(result)
            return results
        
        # Parallel scanning
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_symbol = {
                executor.submit(self.scan_symbol, symbol, timeframe, limit, client): symbol
                for symbol in symbols
            }
            
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error in parallel scan for {symbol}: {e}")
                    results.append({
                        'symbol': symbol,
                        'success': False,
                        'error': str(e),
                        'patterns': []
                    })
        
        return results
    
    async def scan_symbol_async(
        self,
        symbol: str,
        timeframe: str = "D",
        limit: int = 100,
        client: Any = None
    ) -> Dict[str, Any]:
        """
        Async scan a single symbol for harmonic patterns.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe for analysis
            limit: Number of candles to analyze
            client: Fyers API client instance
            
        Returns:
            Dictionary with scan results
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.scan_symbol,
            symbol,
            timeframe,
            limit,
            client
        )
    
    async def scan_multiple_async(
        self,
        symbols: List[str],
        timeframe: str = "D",
        limit: int = 100,
        client: Any = None
    ) -> List[Dict[str, Any]]:
        """
        Async scan multiple symbols for harmonic patterns.
        
        Args:
            symbols: List of trading symbols
            timeframe: Timeframe for analysis
            limit: Number of candles to analyze
            client: Fyers API client instance
            
        Returns:
            List of scan results
        """
        tasks = [
            self.scan_symbol_async(symbol, timeframe, limit, client)
            for symbol in symbols
        ]
        return await asyncio.gather(*tasks)
    
    def scan_watchlist(
        self,
        watchlist: List[str],
        timeframe: str = "D",
        limit: int = 100,
        client: Any = None,
        min_confidence: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Scan a watchlist and return ranked results.
        
        Args:
            watchlist: List of symbols to scan
            timeframe: Timeframe for analysis
            limit: Number of candles to analyze
            client: Fyers API client instance
            min_confidence: Filter patterns by minimum confidence
            
        Returns:
            Dictionary with ranked results and summary
        """
        min_conf = min_confidence or self.min_confidence
        
        # Scan all symbols
        results = self.scan_multiple(watchlist, timeframe, limit, client, parallel=True)
        
        # Filter and rank results
        ranked_results = []
        for result in results:
            if result['success'] and result['has_pattern']:
                # Filter by confidence
                filtered_patterns = [
                    p for p in result['patterns']
                    if p['confidence'] >= min_conf
                ]
                
                if filtered_patterns:
                    # Get best pattern
                    best_pattern = max(filtered_patterns, key=lambda x: x['confidence'])
                    ranked_results.append({
                        'symbol': result['symbol'],
                        'current_price': result['current_price'],
                        'pattern': best_pattern,
                        'all_patterns': filtered_patterns,
                        'score': int(best_pattern['confidence'] * 100)
                    })
        
        # Sort by confidence
        ranked_results.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'total_symbols': len(watchlist),
            'scanned_symbols': len(results),
            'symbols_with_patterns': len(ranked_results),
            'timeframe': timeframe,
            'min_confidence': min_conf,
            'ranked_results': ranked_results
        }
    
    def generate_signal(
        self,
        symbol: str,
        pattern: HarmonicPattern
    ) -> Signal:
        """
        Generate a trading signal from a detected pattern.
        
        Args:
            symbol: Trading symbol
            pattern: Detected harmonic pattern
            
        Returns:
            Signal object
        """
        action = 'BUY' if pattern.direction == 'bullish' else 'SELL'
        score = int(pattern.confidence * 100)
        
        return Signal(
            symbol=symbol,
            action=action,
            score=score,
            price=pattern.entry_price or 0,
            pattern=pattern.name,
            pattern_confidence=pattern.confidence,
            timestamp=pattern.timestamp or pd.Timestamp.now(),
            metadata={
                'stop_loss': pattern.stop_loss,
                'take_profit': pattern.take_profit,
                'risk_reward': pattern.risk_reward,
                'ratios': pattern.ratios
            }
        )
    
    def clear_cache(self):
        """Clear the data and pattern cache."""
        self._data_cache.clear()
        self._pattern_cache.clear()
        logger.info("Scanner cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            'data_cache_size': len(self._data_cache),
            'pattern_cache_size': len(self._pattern_cache),
            'cache_ttl': self.cache_ttl,
            'cache_enabled': self.enable_cache
        }
