"""Portfolio Tracker - Position management, PnL tracking, and portfolio analytics."""
import logging
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PortfolioTracker:
    """
    Portfolio tracking service for managing positions, calculating PnL,
    and providing portfolio analytics.
    """
    
    def __init__(self, initial_capital: Decimal = Decimal('10000')):
        self.initial_capital = initial_capital
    
    def open_position(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        entry_price: Decimal,
        stop_loss: Decimal = None,
        take_profit: Decimal = None,
        signal_id: str = None,
    ) -> Dict:
        """
        Open a new portfolio position.
        
        Returns:
            Dict with position details
        """
        position_value = quantity * entry_price
        
        # Calculate risk amount
        risk_amount = Decimal('0')
        if stop_loss:
            if side == 'long':
                risk_amount = quantity * (entry_price - stop_loss)
            else:
                risk_amount = quantity * (stop_loss - entry_price)
        
        position = {
            'symbol': symbol,
            'side': side,
            'quantity': float(quantity),
            'entry_price': float(entry_price),
            'current_price': float(entry_price),
            'stop_loss': float(stop_loss) if stop_loss else None,
            'take_profit': float(take_profit) if take_profit else None,
            'unrealized_pnl': 0.0,
            'unrealized_pnl_percent': 0.0,
            'risk_amount': float(risk_amount),
            'risk_percent': float((risk_amount / self.initial_capital * 100)) if self.initial_capital > 0 else 0,
            'signal_id': signal_id,
            'is_active': True,
            'opened_at': datetime.now().isoformat(),
        }
        
        logger.info(f"Opened {side} position: {quantity} {symbol} @ {entry_price}")
        return position
    
    def close_position(
        self,
        position: Dict,
        close_price: Decimal,
        reason: str = 'manual',
    ) -> Dict:
        """
        Close a position and calculate realized PnL.
        
        Returns:
            Dict with closed position details and PnL
        """
        entry_price = Decimal(str(position['entry_price']))
        quantity = Decimal(str(position['quantity']))
        side = position['side']
        
        if side == 'long':
            pnl = quantity * (close_price - entry_price)
        else:
            pnl = quantity * (entry_price - close_price)
        
        pnl_percent = (pnl / (quantity * entry_price) * 100) if entry_price > 0 else Decimal('0')
        
        closed = {
            **position,
            'current_price': float(close_price),
            'close_price': float(close_price),
            'close_reason': reason,
            'unrealized_pnl': float(pnl),
            'unrealized_pnl_percent': float(pnl_percent),
            'is_active': False,
            'closed_at': datetime.now().isoformat(),
        }
        
        logger.info(
            f"Closed {side} position: {quantity} {position['symbol']} @ {close_price} "
            f"- PnL: {pnl} ({pnl_percent:.2f}%)"
        )
        return closed
    
    def update_position_price(
        self,
        position: Dict,
        current_price: Decimal,
    ) -> Dict:
        """Update position with current market price."""
        entry_price = Decimal(str(position['entry_price']))
        quantity = Decimal(str(position['quantity']))
        side = position['side']
        
        if side == 'long':
            pnl = quantity * (current_price - entry_price)
        else:
            pnl = quantity * (entry_price - current_price)
        
        pnl_percent = (pnl / (quantity * entry_price) * 100) if entry_price > 0 else Decimal('0')
        
        updated = {
            **position,
            'current_price': float(current_price),
            'unrealized_pnl': float(pnl),
            'unrealized_pnl_percent': float(pnl_percent),
        }
        
        return updated
    
    def calculate_portfolio_metrics(
        self,
        positions: List[Dict],
        closed_positions: List[Dict] = None,
    ) -> Dict:
        """
        Calculate comprehensive portfolio metrics.
        
        Returns:
            Dict with portfolio performance metrics
        """
        closed_positions = closed_positions or []
        
        # Active position metrics
        total_exposure = Decimal('0')
        total_unrealized_pnl = Decimal('0')
        total_risk = Decimal('0')
        
        for pos in positions:
            if pos.get('is_active', True):
                pos_value = Decimal(str(pos['quantity'])) * Decimal(str(pos['current_price']))
                total_exposure += pos_value
                total_unrealized_pnl += Decimal(str(pos.get('unrealized_pnl', 0)))
                total_risk += Decimal(str(pos.get('risk_amount', 0)))
        
        # Closed position metrics
        total_realized_pnl = Decimal('0')
        winning_trades = 0
        losing_trades = 0
        total_trades = len(closed_positions)
        
        for pos in closed_positions:
            pnl = Decimal(str(pos.get('unrealized_pnl', 0)))
            total_realized_pnl += pnl
            if pnl > 0:
                winning_trades += 1
            elif pnl < 0:
                losing_trades += 1
        
        # Calculate derived metrics
        total_pnl = total_realized_pnl + total_unrealized_pnl
        roi = (total_pnl / self.initial_capital * 100) if self.initial_capital > 0 else Decimal('0')
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else Decimal('0')
        avg_win = (
            sum(Decimal(str(p.get('unrealized_pnl', 0))) for p in closed_positions if Decimal(str(p.get('unrealized_pnl', 0))) > 0) /
            winning_trades if winning_trades > 0 else Decimal('0')
        )
        avg_loss = (
            sum(abs(Decimal(str(p.get('unrealized_pnl', 0)))) for p in closed_positions if Decimal(str(p.get('unrealized_pnl', 0))) < 0) /
            losing_trades if losing_trades > 0 else Decimal('0')
        )
        profit_factor = (avg_win / avg_loss) if avg_loss > 0 else Decimal('0')
        
        exposure_pct = (total_exposure / self.initial_capital * 100) if self.initial_capital > 0 else Decimal('0')
        risk_pct = (total_risk / self.initial_capital * 100) if self.initial_capital > 0 else Decimal('0')
        
        return {
            'total_exposure': float(total_exposure),
            'exposure_percent': float(exposure_pct),
            'total_risk': float(total_risk),
            'risk_percent': float(risk_pct),
            'total_unrealized_pnl': float(total_unrealized_pnl),
            'total_realized_pnl': float(total_realized_pnl),
            'total_pnl': float(total_pnl),
            'roi_percent': float(roi),
            'active_positions': len([p for p in positions if p.get('is_active', True)]),
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': float(win_rate),
            'avg_win': float(avg_win),
            'avg_loss': float(avg_loss),
            'profit_factor': float(profit_factor),
        }
    
    def check_position_limits(
        self,
        positions: List[Dict],
        new_position: Dict,
        account_balance: Decimal,
        max_position_pct: Decimal = Decimal('10'),
        max_correlated: int = 3,
    ) -> Dict:
        """
        Check if a new position violates any limits.
        
        Returns:
            Dict with limit check results
        """
        violations = []
        
        # Check position size limit
        new_value = Decimal(str(new_position['quantity'])) * Decimal(str(new_position['entry_price']))
        max_value = account_balance * (max_position_pct / 100)
        
        if new_value > max_value:
            violations.append({
                'type': 'position_size',
                'message': f"Position value {new_value} exceeds max {max_value}",
                'limit': float(max_value),
                'actual': float(new_value),
            })
        
        # Check correlated positions
        base_asset = new_position['symbol'].split('/')[0] if '/' in new_position['symbol'] else new_position['symbol']
        correlated_count = sum(
            1 for p in positions
            if p.get('is_active', True) and
            (p['symbol'].split('/')[0] if '/' in p['symbol'] else p['symbol']) == base_asset
        )
        
        if correlated_count >= max_correlated:
            violations.append({
                'type': 'correlated_positions',
                'message': f"Too many correlated positions ({correlated_count}) for {base_asset}",
                'limit': max_correlated,
                'actual': correlated_count,
            })
        
        # Check total portfolio risk
        total_risk = Decimal(str(new_position.get('risk_amount', 0)))
        for pos in positions:
            if pos.get('is_active', True):
                total_risk += Decimal(str(pos.get('risk_amount', 0)))
        
        risk_pct = (total_risk / account_balance * 100) if account_balance > 0 else Decimal('0')
        if risk_pct > 6:
            violations.append({
                'type': 'portfolio_risk',
                'message': f"Total portfolio risk {risk_pct:.2f}% exceeds 6% limit",
                'limit': 6.0,
                'actual': float(risk_pct),
            })
        
        return {
            'allowed': len(violations) == 0,
            'violations': violations,
            'new_position_value': float(new_value),
        }
    
    def generate_portfolio_summary(
        self,
        positions: List[Dict],
        account_balance: Decimal,
    ) -> Dict:
        """Generate a human-readable portfolio summary."""
        metrics = self.calculate_portfolio_metrics(positions)
        
        # Group positions by side
        long_positions = [p for p in positions if p.get('is_active') and p.get('side') == 'long']
        short_positions = [p for p in positions if p.get('is_active') and p.get('side') == 'short']
        
        # Group by asset
        assets = {}
        for pos in positions:
            if pos.get('is_active'):
                base = pos['symbol'].split('/')[0] if '/' in pos['symbol'] else pos['symbol']
                if base not in assets:
                    assets[base] = {'long': 0, 'short': 0, 'total_value': 0}
                assets[base][pos['side']] += 1
                assets[base]['total_value'] += Decimal(str(pos['quantity'])) * Decimal(str(pos['current_price']))
        
        return {
            'summary': metrics,
            'long_positions': len(long_positions),
            'short_positions': len(short_positions),
            'asset_allocation': {
                k: {'long': v['long'], 'short': v['short'], 'value': float(v['total_value'])}
                for k, v in assets.items()
            },
            'account_balance': float(account_balance),
            'total_portfolio_value': float(account_balance + metrics['total_unrealized_pnl']),
        }
