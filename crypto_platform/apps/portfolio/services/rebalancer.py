"""Portfolio rebalancing service - Automated and manual rebalancing."""
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class PortfolioRebalancer:
    """Handles portfolio rebalancing operations."""
    
    def __init__(self):
        self.min_trade_usd = Decimal('10')  # Minimum trade size
        self.max_slippage_percent = Decimal('0.5')  # Max acceptable slippage
    
    def calculate_rebalance_trades(
        self,
        current_holdings: Dict[str, Decimal],
        target_allocation: Dict[str, Decimal],
        total_value_usd: Decimal,
    ) -> List[Dict]:
        """
        Calculate trades needed to rebalance portfolio.
        
        Args:
            current_holdings: {symbol: value_usd}
            target_allocation: {symbol: target_percent}
            total_value_usd: Total portfolio value
            
        Returns:
            List of trades to execute
        """
        trades = []
        
        # Calculate current percentages
        current_allocation = {}
        for symbol, value in current_holdings.items():
            if total_value_usd > 0:
                current_allocation[symbol] = (value / total_value_usd) * 100
            else:
                current_allocation[symbol] = Decimal('0')
        
        # Calculate target values
        target_values = {}
        for symbol, percent in target_allocation.items():
            target_values[symbol] = total_value_usd * (percent / 100)
        
        # Find all symbols
        all_symbols = set(list(current_holdings.keys()) + list(target_allocation.keys()))
        
        for symbol in all_symbols:
            current_value = current_holdings.get(symbol, Decimal('0'))
            target_value = target_values.get(symbol, Decimal('0'))
            
            difference = target_value - current_value
            
            # Skip small trades
            if abs(difference) < self.min_trade_usd:
                continue
            
            # Determine action
            if difference > 0:
                action = 'buy'
            else:
                action = 'sell'
            
            # Calculate percentage difference
            if current_value > 0:
                percent_diff = (difference / current_value) * 100
            else:
                percent_diff = Decimal('100') if action == 'buy' else Decimal('0')
            
            trades.append({
                'symbol': symbol,
                'action': action,
                'current_value_usd': float(current_value),
                'target_value_usd': float(target_value),
                'trade_value_usd': float(abs(difference)),
                'percent_change': float(percent_diff),
                'current_percent': float(current_allocation.get(symbol, 0)),
                'target_percent': float(target_allocation.get(symbol, 0)),
            })
        
        # Sort by trade value (largest first)
        trades.sort(key=lambda x: x['trade_value_usd'], reverse=True)
        
        logger.info(f"Calculated {len(trades)} rebalance trades for ${total_value_usd}")
        return trades
    
    def check_rebalance_needed(
        self,
        current_allocation: Dict[str, Decimal],
        target_allocation: Dict[str, Decimal],
        threshold_percent: Decimal = Decimal('5'),
    ) -> Tuple[bool, List[Dict]]:
        """
        Check if rebalancing is needed based on drift from target.
        
        Returns:
            Tuple of (needs_rebalance, list of drifted assets)
        """
        drifted = []
        
        for symbol, target in target_allocation.items():
            current = current_allocation.get(symbol, Decimal('0'))
            drift = abs(current - target)
            
            if drift > threshold_percent:
                drifted.append({
                    'symbol': symbol,
                    'current_percent': float(current),
                    'target_percent': float(target),
                    'drift_percent': float(drift),
                })
        
        needs_rebalance = len(drifted) > 0
        
        if needs_rebalance:
            logger.info(f"Rebalance needed: {len(drifted)} assets drifted beyond threshold")
        
        return needs_rebalance, drifted
    
    def optimize_allocation(
        self,
        historical_returns: Dict[str, List[float]],
        risk_tolerance: str = 'moderate',
    ) -> Dict[str, Decimal]:
        """
        Optimize portfolio allocation based on historical returns.
        
        Simple mean-variance optimization.
        
        Args:
            historical_returns: {symbol: [daily_returns]}
            risk_tolerance: 'conservative', 'moderate', 'aggressive'
            
        Returns:
            Optimized allocation percentages
        """
        import numpy as np
        
        # Risk parameters
        risk_params = {
            'conservative': {'max_volatility': 0.3, 'min_return': 0.05},
            'moderate': {'max_volatility': 0.5, 'min_return': 0.10},
            'aggressive': {'max_volatility': 0.8, 'min_return': 0.15},
        }
        params = risk_params.get(risk_tolerance, risk_params['moderate'])
        
        symbols = list(historical_returns.keys())
        n = len(symbols)
        
        if n == 0:
            return {}
        
        # Calculate returns and volatility
        returns = {}
        volatilities = {}
        
        for symbol, returns_list in historical_returns.items():
            if len(returns_list) > 0:
                returns[symbol] = np.mean(returns_list)
                volatilities[symbol] = np.std(returns_list) if len(returns_list) > 1 else 0.1
            else:
                returns[symbol] = 0
                volatilities[symbol] = 0.5
        
        # Simple optimization: weight by return/volatility (Sharpe-like)
        scores = {}
        for symbol in symbols:
            vol = max(volatilities[symbol], 0.01)  # Avoid division by zero
            scores[symbol] = returns[symbol] / vol
        
        # Normalize to 100%
        total_score = sum(max(score, 0) for score in scores.values())
        
        if total_score == 0:
            # Equal weight if no positive scores
            allocation = {symbol: Decimal(str(100 / n)) for symbol in symbols}
        else:
            allocation = {}
            for symbol in symbols:
                score = max(scores[symbol], 0)
                allocation[symbol] = Decimal(str(round(score / total_score * 100, 2)))
        
        # Ensure allocation sums to 100%
        total = sum(allocation.values())
        if total != 100 and total > 0:
            factor = Decimal('100') / total
            allocation = {k: round(v * factor, 2) for k, v in allocation.items()}
        
        logger.info(f"Optimized allocation: {allocation}")
        return allocation
