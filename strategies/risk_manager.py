"""
Risk Management Module for QuantWave.
Handles position sizing, risk limits, and portfolio management.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Represents an open trading position."""
    symbol: str
    side: str  # 'BUY' or 'SELL'
    quantity: int
    entry_price: float
    current_price: float
    pnl: float = 0.0
    entry_time: Optional[str] = None


class RiskManager:
    """
    Risk management controller.
    
    Enforces risk limits, calculates position sizes, and manages open positions.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Risk Manager.
        
        Args:
            config: Configuration dictionary with risk parameters
        """
        self.config = config
        self.positions: Dict[str, Position] = {}
        self.daily_trades: List[Dict] = []
        self.daily_pnl: float = 0.0
        
        # Risk parameters
        self.risk_per_trade = config.get("risk_per_trade", 0.01)
        self.max_positions = config.get("max_positions", 5)
        self.max_daily_loss = config.get("max_daily_loss", 0.03)
        self.max_trades_per_day = config.get("max_trades_per_day", 10)
        self.capital = config.get("capital", 100000)
        
    def can_trade(self, symbol: str) -> tuple[bool, str]:
        """
        Check if a new trade can be opened.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Tuple of (can_trade, reason)
        """
        # Check max positions
        if len(self.positions) >= self.max_positions:
            return False, f"Max positions ({self.max_positions}) reached"
        
        # Check daily trade limit
        if len(self.daily_trades) >= self.max_trades_per_day:
            return False, f"Daily trade limit ({self.max_trades_per_day}) reached"
        
        # Check daily loss limit
        if self.daily_pnl < 0 and abs(self.daily_pnl) / self.capital >= self.max_daily_loss:
            return False, f"Daily loss limit ({self.max_daily_loss * 100}%) reached"
        
        # Check if position already exists
        if symbol in self.positions:
            return False, f"Position already open for {symbol}"
        
        return True, "OK"
    
    def calculate_position_size(self, price: float, stop_loss: float) -> int:
        """
        Calculate position size based on risk per trade.
        
        Args:
            price: Entry price
            stop_loss: Stop loss price
            
        Returns:
            Quantity to trade
        """
        risk_amount = self.capital * self.risk_per_trade
        risk_per_share = abs(price - stop_loss)
        
        if risk_per_share == 0:
            return 0
        
        quantity = int(risk_amount / risk_per_share)
        
        # Round to nearest lot size (assuming 1 lot = 1 share for simplicity)
        return max(0, quantity)
    
    def add_position(self, position: Position) -> None:
        """
        Add a new position.
        
        Args:
            position: Position object
        """
        self.positions[position.symbol] = position
        logger.info(f"Added position: {position.symbol} {position.side} {position.quantity} @ {position.entry_price}")
    
    def remove_position(self, symbol: str) -> Optional[Position]:
        """
        Remove a position.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Removed position or None
        """
        position = self.positions.pop(symbol, None)
        if position:
            logger.info(f"Removed position: {symbol}")
        return position
    
    def update_position_pnl(self, symbol: str, current_price: float) -> None:
        """
        Update P&L for a position.
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
        """
        if symbol in self.positions:
            position = self.positions[symbol]
            position.current_price = current_price
            
            if position.side == "BUY":
                position.pnl = (current_price - position.entry_price) * position.quantity
            else:  # SELL
                position.pnl = (position.entry_price - current_price) * position.quantity
    
    def get_open_positions(self) -> List[Position]:
        """
        Get all open positions.
        
        Returns:
            List of open positions
        """
        return list(self.positions.values())
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get a specific position.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Position object or None
        """
        return self.positions.get(symbol)
    
    def record_trade(self, trade: Dict[str, Any]) -> None:
        """
        Record a completed trade.
        
        Args:
            trade: Trade dictionary with trade details
        """
        self.daily_trades.append(trade)
        self.daily_pnl += trade.get("pnl", 0)
        logger.info(f"Recorded trade: {trade.get('symbol')} P&L: {trade.get('pnl')}")
    
    def get_daily_summary(self) -> Dict[str, Any]:
        """
        Get daily trading summary.
        
        Returns:
            Dictionary with daily statistics
        """
        return {
            "trades_today": len(self.daily_trades),
            "daily_pnl": self.daily_pnl,
            "daily_pnl_pct": (self.daily_pnl / self.capital) * 100,
            "open_positions": len(self.positions),
            "capital": self.capital,
        }
