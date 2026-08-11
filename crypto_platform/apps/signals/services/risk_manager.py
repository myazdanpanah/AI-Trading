"""Risk Manager - Position sizing, portfolio risk management, and Kelly Criterion."""
import logging
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RiskManager:
    """
    Risk management service for position sizing, portfolio risk assessment,
    and drawdown protection.
    """
    
    def __init__(self, risk_profile=None):
        self.profile = risk_profile
    
    _defaults = {
        'max_portfolio_risk': Decimal('2.0'),
        'max_position_size': Decimal('10.0'),
        'max_correlated_positions': Decimal('3'),
        'max_drawdown': Decimal('10.0'),
        'risk_per_trade': Decimal('1.0'),
        'use_kelly_criterion': False,
        'kelly_fraction': Decimal('0.25'),
    }
    
    def calculate_position_size(
        self,
        account_balance: Decimal,
        entry_price: Decimal,
        stop_loss: Decimal,
        signal_confidence: int,
        signal_direction: str,
        current_positions: List[Dict] = None,
    ) -> Dict:
        """
        Calculate optimal position size based on risk parameters.
        
        Returns:
            Dict with position_size, risk_amount, and sizing details
        """
        risk_per_trade = self._get_param('risk_per_trade')
        max_position = self._get_param('max_position_size')
        
        # Calculate risk per unit
        if signal_direction in ('buy', 'strong_buy'):
            risk_per_unit = entry_price - stop_loss
        elif signal_direction in ('sell', 'strong_sell'):
            risk_per_unit = stop_loss - entry_price
        else:
            return {'position_size': 0, 'error': 'No valid direction'}
        
        if risk_per_unit <= 0:
            return {'position_size': 0, 'error': 'Invalid stop loss level'}
        
        # Base position sizing: risk amount / risk per unit
        risk_amount = account_balance * (risk_per_trade / Decimal('100'))
        position_size = risk_amount / risk_per_unit
        
        # Adjust for signal confidence
        confidence_factor = Decimal(str(signal_confidence)) / Decimal('100')
        adjusted_size = position_size * (Decimal('0.5') + (confidence_factor * Decimal('0.5')))
        
        # Check maximum position size (as % of account)
        max_size_by_pct = (account_balance * (max_position / Decimal('100'))) / entry_price
        position_value = adjusted_size * entry_price
        
        if position_value > (account_balance * max_position / Decimal('100')):
            adjusted_size = max_size_by_pct
        
        # Apply Kelly Criterion if enabled
        if self._get_param('use_kelly_criterion'):
            kelly_size = self._kelly_criterion(
                win_rate=Decimal('0.55'),  # Default win rate
                avg_win=Decimal('1.5'),    # Default avg win
                avg_loss=Decimal('1.0'),   # Default avg loss
            )
            kelly_fraction = self._get_param('kelly_fraction')
            kelly_adjusted = adjusted_size * kelly_fraction
            adjusted_size = min(adjusted_size, kelly_adjusted)
        
        # Check portfolio-level limits
        current_positions = current_positions or []
        portfolio_check = self._check_portfolio_limits(
            adjusted_size, entry_price, current_positions, account_balance
        )
        if portfolio_check.get('exceeds_limit'):
            adjusted_size = portfolio_check.get('adjusted_size', adjusted_size)
        
        final_risk = adjusted_size * risk_per_unit
        final_risk_pct = (final_risk / account_balance) * Decimal('100')
        
        return {
            'position_size': float(adjusted_size),
            'position_value': float(adjusted_size * entry_price),
            'risk_amount': float(final_risk),
            'risk_percent': float(final_risk_pct),
            'risk_per_unit': float(risk_per_unit),
            'stop_distance_pct': float((risk_per_unit / entry_price) * Decimal('100')),
            'account_balance': float(account_balance),
            'within_limits': final_risk_pct <= risk_per_trade,
        }
    
    def assess_portfolio_risk(
        self,
        account_balance: Decimal,
        current_positions: List[Dict],
    ) -> Dict:
        """
        Assess overall portfolio risk.
        
        Returns:
            Dict with portfolio risk metrics
        """
        total_exposure = Decimal('0')
        total_risk = Decimal('0')
        correlation_groups = {}
        
        for pos in current_positions:
            pos_value = Decimal(str(pos.get('quantity', 0))) * Decimal(str(pos.get('current_price', 0)))
            pos_risk = Decimal(str(pos.get('risk_amount', 0)))
            symbol = pos.get('symbol', '')
            
            total_exposure += pos_value
            total_risk += pos_risk
            
            # Group by base asset for correlation
            base = symbol.split('/')[0] if '/' in symbol else symbol
            if base not in correlation_groups:
                correlation_groups[base] = []
            correlation_groups[base].append(pos)
        
        exposure_pct = (total_exposure / account_balance * Decimal('100')) if account_balance > 0 else Decimal('0')
        risk_pct = (total_risk / account_balance * Decimal('100')) if account_balance > 0 else Decimal('0')
        
        # Check max correlated positions
        max_correlated = int(self._get_param('max_correlated_positions'))
        correlated_violations = {
            k: len(v) for k, v in correlation_groups.items() if len(v) > max_correlated
        }
        
        # Check max drawdown
        unrealized_pnl = sum(
            Decimal(str(pos.get('unrealized_pnl', 0))) for pos in current_positions
        )
        drawdown_pct = (abs(unrealized_pnl) / account_balance * Decimal('100')) if unrealized_pnl < 0 and account_balance > 0 else Decimal('0')
        max_dd = self._get_param('max_drawdown')
        
        risk_level = 'low'
        if risk_pct > self._get_param('risk_per_trade') * 2:
            risk_level = 'high'
        elif risk_pct > self._get_param('risk_per_trade'):
            risk_level = 'medium'
        
        return {
            'total_exposure': float(total_exposure),
            'exposure_percent': float(exposure_pct),
            'total_risk': float(total_risk),
            'risk_percent': float(risk_pct),
            'unrealized_pnl': float(unrealized_pnl),
            'drawdown_percent': float(drawdown_pct),
            'position_count': len(current_positions),
            'correlated_violations': correlated_violations,
            'risk_level': risk_level,
            'within_limits': (
                risk_pct <= self._get_param('risk_per_trade') * 3 and
                drawdown_pct <= max_dd and
                not correlated_violations
            ),
        }
    
    def calculate_risk_reward_ratio(
        self,
        entry_price: Decimal,
        stop_loss: Decimal,
        take_profit: Decimal,
    ) -> Dict:
        """Calculate risk/reward ratio for a trade."""
        if entry_price <= 0 or stop_loss <= 0 or take_profit <= 0:
            return {'ratio': 0, 'error': 'Invalid price levels'}
        
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        
        if risk == 0:
            return {'ratio': 0, 'error': 'Zero risk (stop loss at entry)'}
        
        ratio = reward / risk
        
        return {
            'ratio': float(ratio),
            'risk': float(risk),
            'reward': float(reward),
            'risk_percent': float((risk / entry_price) * Decimal('100')),
            'reward_percent': float((reward / entry_price) * Decimal('100')),
            'favorable': ratio >= Decimal('2'),
        }
    
    def check_stop_loss_triggers(
        self,
        current_positions: List[Dict],
        current_prices: Dict[str, Decimal],
    ) -> List[Dict]:
        """Check if any positions have triggered stop loss."""
        triggers = []
        
        for pos in current_positions:
            symbol = pos.get('symbol')
            stop_loss = pos.get('stop_loss')
            current_price = current_prices.get(symbol)
            
            if not stop_loss or not current_price:
                continue
            
            stop_loss = Decimal(str(stop_loss))
            current_price = Decimal(str(current_price))
            side = pos.get('side', 'long')
            
            triggered = False
            if side == 'long' and current_price <= stop_loss:
                triggered = True
            elif side == 'short' and current_price >= stop_loss:
                triggered = True
            
            if triggered:
                triggers.append({
                    'position_id': pos.get('id'),
                    'symbol': symbol,
                    'side': side,
                    'stop_loss': float(stop_loss),
                    'current_price': float(current_price),
                    'action': 'close_position',
                    'reason': 'stop_loss_triggered',
                })
        
        return triggers
    
    def _kelly_criterion(
        self,
        win_rate: Decimal,
        avg_win: Decimal,
        avg_loss: Decimal,
    ) -> Decimal:
        """Calculate Kelly Criterion for optimal position sizing."""
        if avg_loss == 0:
            return Decimal('0')
        
        b = avg_win / avg_loss  # Win/loss ratio
        kelly = (win_rate * b - (Decimal('1') - win_rate)) / b
        
        return max(Decimal('0'), kelly)
    
    def _check_portfolio_limits(
        self,
        position_size: Decimal,
        entry_price: Decimal,
        current_positions: List[Dict],
        account_balance: Decimal,
    ) -> Dict:
        """Check if position size exceeds portfolio limits."""
        max_position = self._get_param('max_position_size')
        new_position_value = position_size * entry_price
        max_value = account_balance * (max_position / Decimal('100'))
        
        if new_position_value > max_value:
            adjusted_size = max_value / entry_price
            return {
                'exceeds_limit': True,
                'adjusted_size': adjusted_size,
                'reason': 'max_position_size',
            }
        
        return {'exceeds_limit': False}
    
    def _get_param(self, name: str) -> Decimal:
        """Get parameter from profile or default."""
        if self.profile:
            val = getattr(self.profile, name, None)
            if val is not None:
                return Decimal(str(val))
        return self._defaults.get(name, Decimal('0'))
