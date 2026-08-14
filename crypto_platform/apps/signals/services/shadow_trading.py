"""Shadow Trading Engine — real market data with simulated execution.

Shadow mode:
    Real Market Data → Real Signal → Real Risk Calc → Simulated Execution
    No real capital is used.

Tracks:
    - Expected price vs actual market price at signal time
    - Simulated fill vs what fill would have been
    - Slippage and spread impact
    - Execution quality score
    - PnL comparison (expected vs simulated)

Architecture:
    ShadowTradingEngine
        ├── Uses real market data (CoinGecko, etc.)
        ├── Simulates execution (like PaperTrading)
        ├── Tracks expected vs actual
        └── Calculates execution quality metrics

Usage:
    engine = ShadowTradingEngine()
    result = engine.shadow_signal(
        symbol='BTCUSDT',
        signal_direction='buy',
        signal_confidence=75,
        expected_entry=50000,
    )
    # result tracks what actually happened vs expected
"""
import logging
import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ShadowTrade:
    """A shadow trade — tracks expected vs actual execution."""
    id: str
    symbol: str
    side: str

    # Expected (from signal)
    expected_entry: float
    expected_exit: float
    expected_pnl: float
    expected_pnl_pct: float

    # Actual (simulated with real data)
    actual_entry: float
    actual_exit: float
    actual_pnl: float
    actual_pnl_pct: float

    # Quality metrics
    entry_slippage: float  # actual_entry - expected_entry (bps)
    exit_slippage: float  # actual_exit - expected_exit (bps)
    total_slippage_bps: float
    execution_quality_score: float  # 0-100, 100 = perfect

    # Metadata
    signal_confidence: int
    signal_id: Optional[str] = None
    holding_period_seconds: int = 0
    close_reason: str = ''
    opened_at: str = ''
    closed_at: str = ''

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'symbol': self.symbol,
            'side': self.side,
            'expected_entry': round(self.expected_entry, 2),
            'expected_exit': round(self.expected_exit, 2),
            'expected_pnl': round(self.expected_pnl, 2),
            'expected_pnl_pct': round(self.expected_pnl_pct, 4),
            'actual_entry': round(self.actual_entry, 2),
            'actual_exit': round(self.actual_exit, 2),
            'actual_pnl': round(self.actual_pnl, 2),
            'actual_pnl_pct': round(self.actual_pnl_pct, 4),
            'entry_slippage_bps': round(self.entry_slippage, 2),
            'exit_slippage_bps': round(self.exit_slippage, 2),
            'total_slippage_bps': round(self.total_slippage_bps, 2),
            'execution_quality_score': round(self.execution_quality_score, 2),
            'signal_confidence': self.signal_confidence,
            'signal_id': self.signal_id,
            'holding_period_seconds': self.holding_period_seconds,
            'close_reason': self.close_reason,
            'opened_at': self.opened_at,
            'closed_at': self.closed_at,
        }


@dataclass
class ShadowAccount:
    """Shadow trading account state."""
    initial_capital: float = 10000.0
    shadow_trades: List[ShadowTrade] = field(default_factory=list)
    active_shadows: Dict[str, Dict] = field(default_factory=dict)
    created_at: str = ''

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    @property
    def total_trades(self) -> int:
        return len(self.shadow_trades)

    @property
    def winning_trades(self) -> int:
        return sum(1 for t in self.shadow_trades if t.actual_pnl > 0)

    @property
    def losing_trades(self) -> int:
        return sum(1 for t in self.shadow_trades if t.actual_pnl <= 0)

    @property
    def win_rate(self) -> float:
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100

    @property
    def avg_execution_quality(self) -> float:
        if not self.shadow_trades:
            return 0.0
        return sum(t.execution_quality_score for t in self.shadow_trades) / len(self.shadow_trades)

    @property
    def avg_slippage_bps(self) -> float:
        if not self.shadow_trades:
            return 0.0
        return sum(t.total_slippage_bps for t in self.shadow_trades) / len(self.shadow_trades)

    @property
    def total_pnl(self) -> float:
        return sum(t.actual_pnl for t in self.shadow_trades)

    @property
    def total_expected_pnl(self) -> float:
        return sum(t.expected_pnl for t in self.shadow_trades)

    @property
    def pnl_accuracy(self) -> float:
        """How close actual PnL was to expected PnL (0-100%)."""
        if not self.shadow_trades or self.total_expected_pnl == 0:
            return 0.0
        total_expected = abs(self.total_expected_pnl)
        total_actual = abs(self.total_pnl)
        if total_expected == 0:
            return 100.0
        accuracy = 1.0 - abs(total_expected - total_actual) / total_expected
        return max(0, min(100, accuracy * 100))

    def to_dict(self) -> Dict:
        return {
            'initial_capital': round(self.initial_capital, 2),
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': round(self.win_rate, 2),
            'total_pnl': round(self.total_pnl, 2),
            'total_expected_pnl': round(self.total_expected_pnl, 2),
            'pnl_accuracy': round(self.pnl_accuracy, 2),
            'avg_execution_quality': round(self.avg_execution_quality, 2),
            'avg_slippage_bps': round(self.avg_slippage_bps, 2),
            'recent_trades': [t.to_dict() for t in self.shadow_trades[-20:]],
            'created_at': self.created_at,
        }


# ── Shadow Trading Engine ─────────────────────────────────────────────

class ShadowTradingEngine:
    """Shadow trading with real market data and simulated execution.

    Shadow mode tracks:
    1. What the signal expected (entry, exit, PnL)
    2. What actually happened (real price, simulated fill)
    3. Execution quality (slippage, spread impact)
    """

    def __init__(
        self,
        initial_capital: float = 10000.0,
        fee_rate: float = 0.001,
        slippage_rate: float = 0.0005,
    ):
        self.initial_capital = initial_capital
        self.fee_rate = fee_rate
        self.slippage_rate = slippage_rate
        self._counter = 0
        self.account = ShadowAccount(initial_capital=initial_capital)

    def shadow_signal(
        self,
        symbol: str,
        side: str,
        signal_confidence: int,
        expected_entry: float,
        expected_exit: float = None,
        signal_id: str = None,
        current_price: float = None,
        spread_bps: float = 5.0,
    ) -> Dict:
        """Record a shadow trade from a signal.

        Args:
            symbol: Trading pair
            side: 'long' or 'short'
            signal_confidence: Signal confidence (0-100)
            expected_entry: Expected entry price from signal
            expected_exit: Expected exit price (if available)
            signal_id: Source signal ID
            current_price: Current market price (if different from expected)
            spread_bps: Bid-ask spread in basis points

        Returns:
            Dict with shadow trade details
        """
        # ── Calculate actual entry with slippage ─────────────────────
        actual_price = current_price or expected_entry

        if side == 'long':
            # Long: buy at ask (entry + spread/2 + slippage)
            spread_impact = actual_price * (spread_bps / 10000 / 2)
            slippage_impact = actual_price * self.slippage_rate
            actual_entry = actual_price + spread_impact + slippage_impact
        else:
            # Short: sell at bid (entry - spread/2 - slippage)
            spread_impact = actual_price * (spread_bps / 10000 / 2)
            slippage_impact = actual_price * self.slippage_rate
            actual_entry = actual_price - spread_impact - slippage_impact

        # ── Calculate entry slippage in basis points ─────────────────
        entry_slippage_bps = ((actual_entry - expected_entry) / expected_entry) * 10000

        # ── Expected PnL ─────────────────────────────────────────────
        if expected_exit:
            if side == 'long':
                expected_pnl_pct = (expected_exit - expected_entry) / expected_entry
            else:
                expected_pnl_pct = (expected_entry - expected_exit) / expected_entry
        else:
            expected_pnl_pct = 0.0

        expected_pnl = self.initial_capital * 0.02 * expected_pnl_pct  # Assume 2% position

        # ── Actual PnL (with slippage) ───────────────────────────────
        # For now, assume exit at expected_exit (or current if not set)
        actual_exit = expected_exit or actual_price
        if side == 'long':
            actual_pnl_pct = (actual_exit - actual_entry) / actual_entry
        else:
            actual_pnl_pct = (actual_entry - actual_exit) / actual_entry

        actual_pnl = self.initial_capital * 0.02 * actual_pnl_pct

        # ── Exit slippage ────────────────────────────────────────────
        if expected_exit:
            exit_slippage_bps = ((actual_exit - expected_exit) / expected_exit) * 10000
        else:
            exit_slippage_bps = 0.0

        total_slippage_bps = abs(entry_slippage_bps) + abs(exit_slippage_bps)

        # ── Execution quality score ──────────────────────────────────
        exec_quality = self._calculate_execution_quality(
            expected_entry, actual_entry, expected_exit, actual_exit, spread_bps
        )

        # ── Create shadow trade ──────────────────────────────────────
        self._counter += 1
        trade_id = f"SHADOW-{self._counter:06d}"

        trade = ShadowTrade(
            id=trade_id,
            symbol=symbol,
            side=side,
            expected_entry=expected_entry,
            expected_exit=expected_exit or 0,
            expected_pnl=expected_pnl,
            expected_pnl_pct=expected_pnl_pct * 100,
            actual_entry=actual_entry,
            actual_exit=actual_exit,
            actual_pnl=actual_pnl,
            actual_pnl_pct=actual_pnl_pct * 100,
            entry_slippage=entry_slippage_bps,
            exit_slippage=exit_slippage_bps,
            total_slippage_bps=total_slippage_bps,
            execution_quality_score=exec_quality,
            signal_confidence=signal_confidence,
            signal_id=signal_id,
            opened_at=datetime.now().isoformat(),
        )

        self.account.shadow_trades.append(trade)

        logger.info(
            f"Shadow trade: {trade_id} {side} {symbol} | "
            f"Expected: {expected_entry:.2f} → Actual: {actual_entry:.2f} | "
            f"Slippage: {total_slippage_bps:.1f} bps | Quality: {exec_quality:.0f}"
        )

        return {
            'success': True,
            'trade': trade.to_dict(),
        }

    def get_status(self) -> Dict:
        """Get shadow trading account status."""
        return self.account.to_dict()

    def get_execution_quality_report(self) -> Dict:
        """Get detailed execution quality analysis."""
        trades = self.account.shadow_trades
        if not trades:
            return {'message': 'No shadow trades yet'}

        # Slippage distribution
        entry_slippages = [abs(t.entry_slippage) for t in trades]
        exit_slippages = [abs(t.exit_slippage) for t in trades]
        qualities = [t.execution_quality_score for t in trades]

        # By symbol
        by_symbol = {}
        for t in trades:
            if t.symbol not in by_symbol:
                by_symbol[t.symbol] = {'trades': 0, 'avg_quality': 0, 'avg_slippage': 0}
            by_symbol[t.symbol]['trades'] += 1
            by_symbol[t.symbol]['avg_quality'] += t.execution_quality_score
            by_symbol[t.symbol]['avg_slippage'] += t.total_slippage_bps

        for sym in by_symbol:
            count = by_symbol[sym]['trades']
            by_symbol[sym]['avg_quality'] = round(by_symbol[sym]['avg_quality'] / count, 2)
            by_symbol[sym]['avg_slippage'] = round(by_symbol[sym]['avg_slippage'] / count, 2)

        return {
            'total_trades': len(trades),
            'avg_entry_slippage_bps': round(sum(entry_slippages) / len(entry_slippages), 2),
            'avg_exit_slippage_bps': round(sum(exit_slippages) / len(exit_slippages), 2),
            'avg_execution_quality': round(sum(qualities) / len(qualities), 2),
            'min_execution_quality': round(min(qualities), 2),
            'max_execution_quality': round(max(qualities), 2),
            'pnl_accuracy': round(self.account.pnl_accuracy, 2),
            'by_symbol': by_symbol,
        }

    def _calculate_execution_quality(
        self,
        expected_entry: float,
        actual_entry: float,
        expected_exit: float,
        actual_exit: float,
        spread_bps: float,
    ) -> float:
        """Calculate execution quality score (0-100).

        Score is based on:
        1. Entry slippage (lower is better)
        2. Exit slippage (lower is better)
        3. Spread impact (lower is better)
        """
        # Entry quality (0-40 points)
        entry_slippage_pct = abs(actual_entry - expected_entry) / expected_entry * 100
        entry_quality = max(0, 40 - entry_slippage_pct * 1000)  # -0.1% = -100 points

        # Exit quality (0-40 points)
        if expected_exit and expected_exit > 0:
            exit_slippage_pct = abs(actual_exit - expected_exit) / expected_exit * 100
            exit_quality = max(0, 40 - exit_slippage_pct * 1000)
        else:
            exit_quality = 20  # Neutral if no expected exit

        # Spread quality (0-20 points)
        spread_quality = max(0, 20 - spread_bps * 0.5)

        total = entry_quality + exit_quality + spread_quality
        return max(0, min(100, total))
