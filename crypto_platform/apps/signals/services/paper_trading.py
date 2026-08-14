"""Paper Trading Engine — simulated execution using same pipeline as live.

Architecture:
    Signal Generation
        ↓
    Risk Engine (same as live)
        ↓
    Paper Execution (simulated fills)
        ↓
    Position Tracking
        ↓
    PnL Calculation
        ↓
    Performance Metrics

Paper trading uses:
    - Same signal generation pipeline
    - Same risk engine validation
    - Same position sizing
    - Simulated fills with configurable fees and slippage
    - Real-time price updates for position valuation

This is identical to live trading except the execution target:
    Live:   Exchange API → Real fills
    Paper:  PaperExecutionProvider → Simulated fills

Usage:
    engine = PaperTradingEngine(initial_capital=10000)
    result = engine.open_position(
        symbol='BTCUSDT',
        side='long',
        signal_confidence=75,
        entry_price=50000,
        stop_loss=49000,
        take_profit=52000,
    )
"""
import logging
import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


# ── Configuration ─────────────────────────────────────────────────────

DEFAULT_FEE_RATE = 0.001       # 0.1% per trade (Binance default)
DEFAULT_SLIPPAGE_RATE = 0.0005 # 0.05% slippage
DEFAULT_INITIAL_CAPITAL = 10000.0
MAX_OPEN_POSITIONS = 10
MAX_POSITION_RISK_PCT = 2.0    # Max 2% risk per position


@dataclass
class PaperPosition:
    """A simulated position in paper trading."""
    id: str
    symbol: str
    side: str  # 'long' or 'short'
    quantity: float
    entry_price: float
    current_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    fees_paid: float = 0.0
    slippage_cost: float = 0.0
    signal_confidence: int = 50
    signal_id: Optional[str] = None
    opened_at: str = ''
    closed_at: Optional[str] = None
    close_price: Optional[float] = None
    close_reason: Optional[str] = None

    @property
    def notional_value(self) -> float:
        return self.quantity * self.current_price

    @property
    def unrealized_pnl(self) -> float:
        if self.side == 'long':
            return (self.current_price - self.entry_price) * self.quantity
        else:
            return (self.entry_price - self.current_price) * self.quantity

    @property
    def unrealized_pnl_pct(self) -> float:
        cost = self.entry_price * self.quantity
        if cost == 0:
            return 0.0
        return (self.unrealized_pnl / cost) * 100

    @property
    def total_cost(self) -> float:
        return self.fees_paid + self.slippage_cost

    @property
    def net_pnl(self) -> float:
        return self.unrealized_pnl - self.total_cost

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'symbol': self.symbol,
            'side': self.side,
            'quantity': round(self.quantity, 8),
            'entry_price': round(self.entry_price, 2),
            'current_price': round(self.current_price, 2),
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'notional_value': round(self.notional_value, 2),
            'unrealized_pnl': round(self.unrealized_pnl, 2),
            'unrealized_pnl_pct': round(self.unrealized_pnl_pct, 2),
            'fees_paid': round(self.fees_paid, 2),
            'slippage_cost': round(self.slippage_cost, 2),
            'net_pnl': round(self.net_pnl, 2),
            'signal_confidence': self.signal_confidence,
            'signal_id': self.signal_id,
            'opened_at': self.opened_at,
            'closed_at': self.closed_at,
            'close_price': self.close_price,
            'close_reason': self.close_reason,
        }


@dataclass
class PaperTrade:
    """A completed (closed) paper trade."""
    id: str
    symbol: str
    side: str
    quantity: float
    entry_price: float
    exit_price: float
    pnl: float
    pnl_pct: float
    fees_paid: float
    slippage_cost: float
    holding_period_seconds: int
    signal_confidence: int
    signal_id: Optional[str] = None
    close_reason: str = ''
    opened_at: str = ''
    closed_at: str = ''

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'symbol': self.symbol,
            'side': self.side,
            'quantity': round(self.quantity, 8),
            'entry_price': round(self.entry_price, 2),
            'exit_price': round(self.exit_price, 2),
            'pnl': round(self.pnl, 2),
            'pnl_pct': round(self.pnl_pct, 2),
            'fees_paid': round(self.fees_paid, 2),
            'slippage_cost': round(self.slippage_cost, 2),
            'total_cost': round(self.fees_paid + self.slippage_cost, 2),
            'holding_period_seconds': self.holding_period_seconds,
            'signal_confidence': self.signal_confidence,
            'signal_id': self.signal_id,
            'close_reason': self.close_reason,
            'opened_at': self.opened_at,
            'closed_at': self.closed_at,
            'was_win': self.pnl > 0,
        }


@dataclass
class PaperAccount:
    """Paper trading account state."""
    initial_capital: float = DEFAULT_INITIAL_CAPITAL
    cash_balance: float = DEFAULT_INITIAL_CAPITAL
    open_positions: Dict[str, PaperPosition] = field(default_factory=dict)
    closed_trades: List[PaperTrade] = field(default_factory=list)
    total_fees_paid: float = 0.0
    total_slippage_cost: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    peak_equity: float = DEFAULT_INITIAL_CAPITAL
    max_drawdown: float = 0.0
    created_at: str = ''

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    @property
    def equity(self) -> float:
        """Total equity = cash + unrealized PnL from open positions."""
        unrealized = sum(p.unrealized_pnl for p in self.open_positions.values())
        return self.cash_balance + unrealized

    @property
    def used_margin(self) -> float:
        """Total margin used by open positions."""
        return sum(p.notional_value for p in self.open_positions.values())

    @property
    def win_rate(self) -> float:
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100

    @property
    def total_return_pct(self) -> float:
        if self.initial_capital == 0:
            return 0.0
        return ((self.equity - self.initial_capital) / self.initial_capital) * 100

    def to_dict(self) -> Dict:
        return {
            'initial_capital': round(self.initial_capital, 2),
            'cash_balance': round(self.cash_balance, 2),
            'equity': round(self.equity, 2),
            'used_margin': round(self.used_margin, 2),
            'open_positions_count': len(self.open_positions),
            'open_positions': [p.to_dict() for p in self.open_positions.values()],
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': round(self.win_rate, 2),
            'total_return_pct': round(self.total_return_pct, 2),
            'total_fees_paid': round(self.total_fees_paid, 2),
            'total_slippage_cost': round(self.total_slippage_cost, 2),
            'peak_equity': round(self.peak_equity, 2),
            'max_drawdown': round(self.max_drawdown, 2),
            'recent_trades': [t.to_dict() for t in self.closed_trades[-10:]],
        }


# ── Paper Trading Engine ──────────────────────────────────────────────

class PaperTradingEngine:
    """Simulated execution engine for paper trading.

    Uses same pipeline as live:
        Signal → Risk Engine → Position Sizing → Execution → Tracking

    But execution is simulated with configurable fees and slippage.
    """

    def __init__(
        self,
        initial_capital: float = DEFAULT_INITIAL_CAPITAL,
        fee_rate: float = DEFAULT_FEE_RATE,
        slippage_rate: float = DEFAULT_SLIPPAGE_RATE,
        max_positions: int = MAX_OPEN_POSITIONS,
        max_risk_pct: float = MAX_POSITION_RISK_PCT,
    ):
        self.fee_rate = fee_rate
        self.slippage_rate = slippage_rate
        self.max_positions = max_positions
        self.max_risk_pct = max_risk_pct

        self.account = PaperAccount(
            initial_capital=initial_capital,
            cash_balance=initial_capital,
        )

        self._position_counter = 0
        self._trade_counter = 0

    def open_position(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        quantity: float = None,
        stop_loss: float = None,
        take_profit: float = None,
        signal_confidence: int = 50,
        signal_id: str = None,
    ) -> Dict:
        """Open a new paper position.

        Args:
            symbol: Trading pair (e.g. 'BTCUSDT')
            side: 'long' or 'short'
            entry_price: Desired entry price
            quantity: Position size (if None, calculated from risk)
            stop_loss: Stop loss price
            take_profit: Take profit price
            signal_confidence: Signal confidence (0-100)
            signal_id: Source signal ID

        Returns:
            Dict with position details and execution info
        """
        # ── Pre-flight checks ────────────────────────────────────────
        if len(self.account.open_positions) >= self.max_positions:
            return {'success': False, 'error': 'Max open positions reached'}

        if side not in ('long', 'short'):
            return {'success': False, 'error': f'Invalid side: {side}'}

        if entry_price <= 0:
            return {'success': False, 'error': 'Invalid entry price'}

        # ── Apply slippage ───────────────────────────────────────────
        if side == 'long':
            fill_price = entry_price * (1 + self.slippage_rate)
        else:
            fill_price = entry_price * (1 - self.slippage_rate)

        # ── Calculate position size ──────────────────────────────────
        if quantity is None:
            quantity = self._calculate_position_size(
                fill_price, stop_loss, signal_confidence
            )

        if quantity <= 0:
            return {'success': False, 'error': 'Calculated quantity is zero'}

        # ── Calculate costs ──────────────────────────────────────────
        notional = quantity * fill_price
        fee = notional * self.fee_rate
        slippage_cost = abs(fill_price - entry_price) * quantity
        total_cost = fee + slippage_cost

        # ── Check margin ─────────────────────────────────────────────
        if total_cost > self.account.cash_balance:
            return {'success': False, 'error': 'Insufficient margin'}

        # ── Execute ──────────────────────────────────────────────────
        self._position_counter += 1
        position_id = f"PAPER-{self._position_counter:06d}"

        position = PaperPosition(
            id=position_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=fill_price,
            current_price=fill_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            fees_paid=fee,
            slippage_cost=slippage_cost,
            signal_confidence=signal_confidence,
            signal_id=signal_id,
            opened_at=datetime.now().isoformat(),
        )

        self.account.open_positions[position_id] = position
        self.account.cash_balance -= total_cost
        self.account.total_fees_paid += fee
        self.account.total_slippage_cost += slippage_cost

        logger.info(
            f"Paper position opened: {position_id} {side} {quantity} {symbol} "
            f"@ {fill_price:.2f} (fee={fee:.2f}, slip={slippage_cost:.2f})"
        )

        return {
            'success': True,
            'position': position.to_dict(),
            'fill_price': round(fill_price, 2),
            'fee': round(fee, 2),
            'slippage_cost': round(slippage_cost, 2),
        }

    def close_position(
        self,
        position_id: str,
        exit_price: float,
        reason: str = 'manual',
    ) -> Dict:
        """Close an existing paper position.

        Args:
            position_id: Position to close
            exit_price: Current market price
            reason: Why closing (manual, stop_loss, take_profit, signal)

        Returns:
            Dict with trade result
        """
        position = self.account.open_positions.get(position_id)
        if not position:
            return {'success': False, 'error': f'Position {position_id} not found'}

        # ── Apply slippage on exit ───────────────────────────────────
        if position.side == 'long':
            fill_price = exit_price * (1 - self.slippage_rate)
        else:
            fill_price = exit_price * (1 + self.slippage_rate)

        # ── Calculate PnL ────────────────────────────────────────────
        if position.side == 'long':
            pnl = (fill_price - position.entry_price) * position.quantity
        else:
            pnl = (position.entry_price - fill_price) * position.quantity

        # ── Calculate exit costs ─────────────────────────────────────
        notional = position.quantity * fill_price
        exit_fee = notional * self.fee_rate
        exit_slippage = abs(fill_price - exit_price) * position.quantity
        total_fees = position.fees_paid + exit_fee
        total_slippage = position.slippage_cost + exit_slippage
        net_pnl = pnl - total_fees - total_slippage

        # ── Calculate holding period ─────────────────────────────────
        opened = datetime.fromisoformat(position.opened_at)
        holding_seconds = int((datetime.now() - opened).total_seconds())

        # ── Create trade record ──────────────────────────────────────
        self._trade_counter += 1
        trade_id = f"TRADE-{self._trade_counter:06d}"

        trade = PaperTrade(
            id=trade_id,
            symbol=position.symbol,
            side=position.side,
            quantity=position.quantity,
            entry_price=position.entry_price,
            exit_price=fill_price,
            pnl=net_pnl,
            pnl_pct=(net_pnl / (position.entry_price * position.quantity)) * 100 if position.entry_price * position.quantity > 0 else 0,
            fees_paid=total_fees,
            slippage_cost=total_slippage,
            holding_period_seconds=holding_seconds,
            signal_confidence=position.signal_confidence,
            signal_id=position.signal_id,
            close_reason=reason,
            opened_at=position.opened_at,
            closed_at=datetime.now().isoformat(),
        )

        # ── Update account ───────────────────────────────────────────
        self.account.cash_balance += position.entry_price * position.quantity + net_pnl
        self.account.closed_trades.append(trade)
        self.account.total_trades += 1
        self.account.total_fees_paid += exit_fee
        self.account.total_slippage_cost += exit_slippage

        if net_pnl > 0:
            self.account.winning_trades += 1
        else:
            self.account.losing_trades += 1

        # Update peak equity and drawdown
        current_equity = self.account.equity
        if current_equity > self.account.peak_equity:
            self.account.peak_equity = current_equity
        drawdown = ((self.account.peak_equity - current_equity) / self.account.peak_equity) * 100
        if drawdown > self.account.max_drawdown:
            self.account.max_drawdown = drawdown

        # Remove position
        del self.account.open_positions[position_id]

        logger.info(
            f"Paper position closed: {position_id} | PnL: {net_pnl:.2f} | "
            f"Reason: {reason} | Holding: {holding_seconds}s"
        )

        return {
            'success': True,
            'trade': trade.to_dict(),
            'account': {
                'cash_balance': round(self.account.cash_balance, 2),
                'equity': round(self.account.equity, 2),
                'total_return_pct': round(self.account.total_return_pct, 2),
            },
        }

    def update_prices(self, prices: Dict[str, float]) -> Dict:
        """Update current prices for all open positions.

        Also checks stop loss and take profit triggers.

        Args:
            prices: {symbol: current_price}

        Returns:
            Dict with triggered exits
        """
        triggered = []

        for pos_id, position in list(self.account.open_positions.items()):
            symbol = position.symbol
            if symbol in prices:
                position.current_price = prices[symbol]

                # Check stop loss
                if position.stop_loss:
                    if position.side == 'long' and position.current_price <= position.stop_loss:
                        result = self.close_position(pos_id, position.current_price, 'stop_loss')
                        if result['success']:
                            triggered.append(result['trade'])
                        continue
                    elif position.side == 'short' and position.current_price >= position.stop_loss:
                        result = self.close_position(pos_id, position.current_price, 'stop_loss')
                        if result['success']:
                            triggered.append(result['trade'])
                        continue

                # Check take profit
                if position.take_profit:
                    if position.side == 'long' and position.current_price >= position.take_profit:
                        result = self.close_position(pos_id, position.current_price, 'take_profit')
                        if result['success']:
                            triggered.append(result['trade'])
                        continue
                    elif position.side == 'short' and position.current_price <= position.take_profit:
                        result = self.close_position(pos_id, position.current_price, 'take_profit')
                        if result['success']:
                            triggered.append(result['trade'])
                        continue

        return {
            'updated_positions': len(self.account.open_positions),
            'triggered_exits': triggered,
        }

    def get_status(self) -> Dict:
        """Get current paper trading account status."""
        return self.account.to_dict()

    def get_performance_metrics(self) -> Dict:
        """Calculate comprehensive performance metrics."""
        trades = self.account.closed_trades
        if not trades:
            return {
                'total_trades': 0,
                'message': 'No completed trades yet',
            }

        pnls = [t.pnl for t in trades]
        pnl_pcts = [t.pnl_pct for t in trades]
        wins = [t for t in trades if t.pnl > 0]
        losses = [t for t in trades if t.pnl <= 0]

        avg_win = sum(t.pnl for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t.pnl for t in losses) / len(losses) if losses else 0

        # Profit factor
        gross_profit = sum(t.pnl for t in wins)
        gross_loss = abs(sum(t.pnl for t in losses))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

        # Expectancy
        expectancy = (self.account.win_rate / 100 * avg_win) + \
                     ((100 - self.account.win_rate) / 100 * avg_loss)

        # Sharpe (simplified, using trade returns)
        if len(pnl_pcts) > 1:
            avg_return = sum(pnl_pcts) / len(pnl_pcts)
            std_return = math.sqrt(sum((r - avg_return) ** 2 for r in pnl_pcts) / (len(pnl_pcts) - 1))
            sharpe = (avg_return / std_return) if std_return > 0 else 0
        else:
            sharpe = 0

        # Average holding period
        avg_holding = sum(t.holding_period_seconds for t in trades) / len(trades)

        return {
            'total_trades': self.account.total_trades,
            'winning_trades': self.account.winning_trades,
            'losing_trades': self.account.losing_trades,
            'win_rate': round(self.account.win_rate, 2),
            'profit_factor': round(profit_factor, 2),
            'expectancy': round(expectancy, 2),
            'sharpe_ratio': round(sharpe, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'avg_holding_period_seconds': round(avg_holding),
            'total_pnl': round(sum(pnls), 2),
            'total_return_pct': round(self.account.total_return_pct, 2),
            'max_drawdown': round(self.account.max_drawdown, 2),
            'total_fees': round(self.account.total_fees_paid, 2),
            'total_slippage': round(self.account.total_slippage_cost, 2),
            'peak_equity': round(self.account.peak_equity, 2),
        }

    def reset(self, initial_capital: float = None) -> Dict:
        """Reset paper trading account."""
        cap = initial_capital or self.account.initial_capital
        self.account = PaperAccount(
            initial_capital=cap,
            cash_balance=cap,
        )
        self._position_counter = 0
        self._trade_counter = 0
        return {'success': True, 'initial_capital': cap}

    # ── Private Helpers ───────────────────────────────────────────────

    def _calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        signal_confidence: int,
    ) -> float:
        """Calculate position size based on risk budget.

        Uses risk-per-trade approach:
            risk_amount = equity * (max_risk_pct / 100)
            stop_distance = abs(entry - stop_loss) / entry
            position_size = risk_amount / (stop_distance * entry)
        """
        equity = self.account.equity
        risk_amount = equity * (self.max_risk_pct / 100)

        # Adjust by confidence (lower confidence → smaller position)
        confidence_factor = signal_confidence / 100.0
        adjusted_risk = risk_amount * confidence_factor

        if stop_loss and stop_loss > 0:
            stop_distance_pct = abs(entry_price - stop_loss) / entry_price
            if stop_distance_pct > 0:
                # Position size = risk_amount / (stop_distance% * entry_price)
                quantity = adjusted_risk / (stop_distance_pct * entry_price)
                return max(0, quantity)

        # Fallback: use a fixed percentage of equity
        # Assume 2% stop loss if none provided
        fallback_risk = adjusted_risk
        fallback_stop_pct = 0.02
        quantity = fallback_risk / (fallback_stop_pct * entry_price)
        return max(0, quantity)
