"""Copy trading service - Automatically copy trades from followed traders."""
import logging
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CopyTrader:
    """Manages copy trading operations."""
    
    def __init__(self):
        self.min_confidence = 70
        self.max_risk_score = 60
    
    def should_copy_signal(
        self,
        signal: Dict,
        follow_config: Dict,
        portfolio_value: Decimal,
    ) -> Dict:
        """
        Determine if a signal should be copied.
        
        Args:
            signal: Signal data from followed trader
            follow_config: Copy trading configuration
            portfolio_value: Current portfolio value
            
        Returns:
            Dict with copy decision and details
        """
        result = {
            'should_copy': False,
            'reason': '',
            'quantity': Decimal('0'),
            'estimated_cost_usd': Decimal('0'),
        }
        
        # Check signal confidence
        confidence = signal.get('confidence', 0)
        if confidence < self.min_confidence:
            result['reason'] = f"Signal confidence {confidence}% below threshold {self.min_confidence}%"
            return result
        
        # Check risk score
        risk_score = signal.get('risk_score', 100)
        if risk_score > self.max_risk_score:
            result['reason'] = f"Risk score {risk_score} above threshold {self.max_risk_score}"
            return result
        
        # Check direction
        direction = signal.get('direction', '')
        if direction not in ['buy', 'strong_buy', 'sell', 'strong_sell']:
            result['reason'] = f"Unsupported direction: {direction}"
            return result
        
        # Calculate position size
        copy_percent = Decimal(str(follow_config.get('copy_position_size_percent', 10)))
        max_copy_amount = Decimal(str(follow_config.get('max_copy_amount_usd', 1000)))
        
        position_value = portfolio_value * (copy_percent / 100)
        position_value = min(position_value, max_copy_amount)
        
        # Calculate quantity
        entry_price = Decimal(str(signal.get('entry_price', 0)))
        if entry_price <= 0:
            result['reason'] = "Invalid entry price"
            return result
        
        quantity = position_value / entry_price
        
        result['should_copy'] = True
        result['reason'] = "Signal meets copy trading criteria"
        result['quantity'] = quantity
        result['estimated_cost_usd'] = position_value
        result['entry_price'] = entry_price
        result['stop_loss'] = signal.get('stop_loss')
        result['take_profit'] = signal.get('take_profit', [])
        
        logger.info(f"Copy trade approved: {signal.get('symbol')} {direction} - ${position_value}")
        return result
    
    def calculate_copy_fee(
        self,
        trade_value: Decimal,
        fee_percent: Decimal,
    ) -> Decimal:
        """Calculate copy trading fee."""
        return trade_value * (fee_percent / 100)
    
    def get_trader_score(self, trader_data: Dict) -> float:
        """
        Calculate a composite score for a trader.
        
        Factors:
        - Win rate (30%)
        - Profit factor (25%)
        - Sharpe ratio (25%)
        - Follower count (20%)
        """
        win_rate = float(trader_data.get('win_rate', 0))
        profit_factor = float(trader_data.get('profit_factor', 0))
        sharpe_ratio = float(trader_data.get('sharpe_ratio', 0))
        followers = int(trader_data.get('followers_count', 0))
        
        # Normalize values
        win_rate_score = min(win_rate / 100, 1.0) * 100
        profit_score = min(profit_factor / 3, 1.0) * 100  # 3.0 is excellent
        sharpe_score = min(sharpe_ratio / 2, 1.0) * 100  # 2.0 is excellent
        followers_score = min(followers / 1000, 1.0) * 100  # 1000 followers is excellent
        
        # Weighted average
        composite_score = (
            win_rate_score * 0.30 +
            profit_score * 0.25 +
            sharpe_score * 0.25 +
            followers_score * 0.20
        )
        
        return round(composite_score, 2)
