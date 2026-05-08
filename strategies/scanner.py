"""Enhanced stock scanner supporting both historical and live modes."""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from .parser import StrategyParser
from .pattern_detector import PatternDetector
from .indicators import calculate_all_indicators, evaluate_strategy, IndicatorValues
from .signal_scorer import SignalScorer, SignalScore
from .smart_money import SmartMoneyStrategy


class StockScanner:
    """Unified scanner for historical backtesting and live trading."""

    def __init__(self, config_path: str = "strategy.json", enable_patterns: bool = True, 
                 enable_scoring: bool = True, enable_smc: bool = False):
        self.parser = StrategyParser(config_path)
        # Use new simplified pattern detector with lower threshold
        self.pattern_detector = PatternDetector(min_pattern_size=5, confidence_threshold=0.5) if enable_patterns else None
        # Signal scorer for probability-based trading
        self.signal_scorer = SignalScorer() if enable_scoring else None
        # Smart Money Concepts strategy
        self.smc_strategy = SmartMoneyStrategy() if enable_smc else None
    
    def calculate_indicators(self, df: pd.DataFrame) -> IndicatorValues:
        """Calculate indicators using shared module."""
        return calculate_all_indicators(df)
    
    def check_entry(self, indicators: IndicatorValues, conditions: Dict) -> bool:
        """Check if entry conditions are met."""
        if not conditions:
            return False
        for key, value in conditions.items():
            if key == "rsi_less_than" and indicators.rsi >= value:
                return False
            elif key == "volume_greater_than" and indicators.volume <= value:
                return False
        return True
    
    def generate_signal(self, indicators: IndicatorValues, entry_conditions: Dict, exit_conditions: Dict) -> str:
        """Generate trading signal based on conditions."""
        if self.check_entry(indicators, entry_conditions):
            return "BUY"
        elif self.check_entry(indicators, exit_conditions):
            return "SELL"
        return "HOLD"
    
    def scan_symbol(self, symbol: str, historical_data: pd.DataFrame) -> Optional[Dict]:
        if historical_data.empty or len(historical_data) < 20:
            return None

        indicators = self.calculate_indicators(historical_data)
        signal = self.generate_signal(indicators, self.parser.get_entry_conditions(), self.parser.get_exit_conditions())

        result = {
            "symbol": symbol,
            "price": indicators.price,
            "signal": signal,
            "rsi": round(indicators.rsi, 2),
            "sma_20": round(indicators.sma_20, 2),
            "volume": int(indicators.volume)
        }

        # Add pattern detection if enabled
        patterns = []
        if self.pattern_detector and len(historical_data) >= 50:
            patterns = self.pattern_detector.detect_all(historical_data)
            if patterns:
                top_pattern = max(patterns, key=lambda p: p["confidence"])
                result["pattern"] = top_pattern["name"]
                result["pattern_confidence"] = round(top_pattern["confidence"], 2)
                result["pattern_direction"] = top_pattern["direction"]
                # Generate pattern-based signal if no indicator signal
                if signal == "HOLD":
                    result["pattern_signal"] = self.pattern_detector.get_combined_signal([top_pattern])
            else:
                result["pattern"] = None  # Explicitly mark no pattern found

        # Add probability scoring if enabled
        if self.signal_scorer:
            score = self.signal_scorer.calculate_score(historical_data, indicators, patterns)
            result["score"] = score.total_score
            result["score_confidence"] = score.confidence
            result["score_breakdown"] = {
                "rsi": score.rsi_score,
                "trend": score.trend_score,
                "volume": score.volume_score,
                "pattern": score.pattern_score
            }
            # Override signal with scored signal if available
            if score.signal != "HOLD":
                result["signal"] = score.signal
                result["signal_source"] = "scored"

        return result
    
    def scan_all(self, fyers_client, symbols: List[str] = None, timeframe: str = None, limit: int = None) -> List[Dict]:
        from api import get_historical_data
        import logging

        logger = logging.getLogger(__name__)

        if limit is None:
            limit = self.parser.get_limit() or 30

        if symbols is None:
            symbols = self.parser.get_symbols()
        if timeframe is None:
            timeframe = self.parser.get_timeframe() or "D"

        print(f"Scanning {len(symbols)} symbols | Timeframe: {timeframe} | Limit: {limit}")
        print(f"Symbols: {symbols}")

        results = []
        for symbol in symbols:
            try:
                print(f"Fetching {symbol}...", end=" ")
                df = get_historical_data(fyers_client, symbol, timeframe, count=limit)
                print(f"Got {len(df)} candles")

                if df.empty:
                    print(f"  [SKIP] No data for {symbol}")
                    continue

                result = self.scan_symbol(symbol, df)
                if result:
                    pattern_str = ""
                    if result.get("pattern"):
                        pattern_str = f" | Pattern: {result['pattern']} ({result['pattern_direction']})"
                    print(f"  [SIGNAL] {result['signal']} - RSI: {result['rsi']}{pattern_str}")
                    results.append(result)
                else:
                    print(f"  [SKIP] Insufficient data")
            except Exception as e:
                print(f"  [ERROR] {e}")
                logger.error(f"Scan error for {symbol}: {e}")
                continue

        print(f"Scan complete. Found {len(results)} signals.")
        return results
    
    def scan_symbol_smc(self, symbol: str, ltf_df: pd.DataFrame, mtf_df: Optional[pd.DataFrame] = None, htf_df: Optional[pd.DataFrame] = None) -> Optional[Dict]:
        """
        Scan a symbol using Smart Money Concepts strategy (3-tier).
        
        Args:
            symbol: Stock symbol
            ltf_df: Lower Time Frame DataFrame (5m)
            mtf_df: Middle Time Frame DataFrame (15m)
            htf_df: Higher Time Frame DataFrame (1h)
            
        Returns:
            SMC result dictionary
        """
        if not self.smc_strategy:
            return None
        
        if ltf_df.empty or len(ltf_df) < 20:
            return None
        
        # Perform SMC analysis
        smc_result = self.smc_strategy.analyze(ltf_df, mtf_df, htf_df)
        smc_result.symbol = symbol
        
        # Build result dictionary
        result = {
            "symbol": symbol,
            "price": ltf_df['close'].iloc[-1],
            "signal": smc_result.signal,
            "score": smc_result.score,
            "htf_aligned": smc_result.htf_aligned,
            "mtf_aligned": smc_result.mtf_aligned,
            "liquidity_sweep": smc_result.liquidity_sweep,
            "mss_confirmed": smc_result.mss_confirmed,
            "fvg_present": smc_result.fvg_present,
            "ob_present": smc_result.ob_present,
            "pattern": smc_result.pattern,
            "details": smc_result.details
        }
        
        return result
    
    def scan_all_smc(self, fyers_client, symbols: List[str] = None, 
                     ltf_timeframe: str = "5m", mtf_timeframe: str = "15m", htf_timeframe: str = "1h",
                     ltf_limit: int = 100, mtf_limit: int = 100, htf_limit: int = 50,
                     min_score: int = 50) -> List[Dict]:
        """
        Scan multiple symbols using 3-tier SMC strategy (1H -> 15M -> 5M).

        Args:
            fyers_client: Fyers API client
            symbols: List of symbols to scan
            ltf_timeframe: Entry TF (e.g., "5m")
            mtf_timeframe: Setup TF (e.g., "15m")
            htf_timeframe: Trend TF (e.g., "1h")
            min_score: Minimum score to include in results (default 50)

        Returns:
            List of SMC scan results
        """
        from api import get_historical_data
        import logging
        import time

        logger = logging.getLogger(__name__)

        if not self.smc_strategy:
            print("ERROR: SMC strategy not enabled. Initialize scanner with enable_smc=True")
            return []

        if symbols is None:
            symbols = self.parser.get_symbols()

        print(f"3-Tier SMC Scan | HTF: {htf_timeframe} | MTF: {mtf_timeframe} | LTF: {ltf_timeframe} | Symbols: {len(symbols)}")

        results = []
        for i, symbol in enumerate(symbols):
            try:
                # Rate limiting
                if i > 0 and i % 5 == 0:
                    time.sleep(2)

                print(f"Scanning {symbol}...")

                # Fetch 3-tier data
                htf_df = get_historical_data(fyers_client, symbol, htf_timeframe, count=htf_limit)
                time.sleep(0.5)
                mtf_df = get_historical_data(fyers_client, symbol, mtf_timeframe, count=mtf_limit)
                time.sleep(0.5)
                ltf_df = get_historical_data(fyers_client, symbol, ltf_timeframe, count=ltf_limit)

                if ltf_df.empty or mtf_df.empty or htf_df.empty:
                    print(f"  [SKIP] Missing data for {symbol}")
                    continue

                # Perform SMC scan
                result = self.scan_symbol_smc(symbol, ltf_df, mtf_df, htf_df)

                if result and result['score'] >= min_score:
                    status = f"HTF:{'✓' if result['htf_aligned'] else '✗'} MTF:{'✓' if result['mtf_aligned'] else '✗'} " \
                             f"Liq:{'✓' if result['liquidity_sweep'] else '✗'} MSS:{'✓' if result['mss_confirmed'] else '✗'}"

                    label = "[STRONG]" if result['score'] >= 75 else "[MODERATE]" if result['score'] >= 60 else "[WEAK]"
                    print(f"  {label} {result['signal']} | Score: {result['score']}% | {status}")
                    results.append(result)
                else:
                    score = result['score'] if result else 0
                    print(f"  [SKIP] Score {score}% below {min_score}%")

            except Exception as e:
                print(f"  [ERROR] {e}")
                logger.error(f"SMC scan error for {symbol}: {e}")
                continue

        print(f"SMC Scan complete. Found {len(results)} setups.")
        return results