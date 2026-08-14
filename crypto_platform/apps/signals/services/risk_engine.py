"""Independent Risk Engine — the safety gate between Signal and Execution.

CRITICAL RULE:
    Signal → Risk → Execution

NEVER:
    Signal → Execution (bypassing Risk)

The Risk Engine is independent from:
- LLM
- Signal Engine
- Strategy
- UI
- Exchange adapter

No AI component may bypass Risk Engine validation.
"""
import logging
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RiskDecision:
    """Result of a risk engine evaluation."""
    approved: bool
    modified: bool = False  # True if position was resized
    reason: str = ''
    position_size: float = 0.0
    risk_amount: float = 0.0
    risk_percent: float = 0.0
    adjusted_size: Optional[float] = None
    kill_switch_active: bool = False
    risk_state: Dict = None

    def __post_init__(self):
        if self.risk_state is None:
            self.risk_state = {}


class RiskEngine:
    """
    Independent Risk Engine — must be the ONLY path between Signal and Execution.

    Responsibilities:
    1. Validate every signal before execution
    2. Calculate position size based on risk budgets
    3. Enforce portfolio exposure limits
    4. Enforce drawdown limits
    5. Enforce daily loss limits
    6. Enforce maximum concurrent positions
    7. Activate kill switch when limits are breached
    8. Log all risk decisions

    The kill switch is INDEPENDENT from:
    - LLM outputs
    - Signal engine
    - Strategy logic
    - User interface
    """

    def __init__(self, config=None):
        """
        Args:
            config: RiskConfig model instance. If None, uses defaults.
        """
        self.config = config
        self._kill_switch_active = False
        self._kill_switch_reason = ''

        # Defaults (used if no config provided)
        self.defaults = {
            'max_risk_per_trade': Decimal('1.0'),
            'max_position_size_pct': Decimal('10.0'),
            'max_concurrent_positions': 5,
            'max_correlated_positions': 3,
            'max_portfolio_risk_pct': Decimal('5.0'),
            'max_portfolio_exposure_pct': Decimal('50.0'),
            'max_drawdown_pct': Decimal('15.0'),
            'daily_loss_limit_pct': Decimal('3.0'),
        }

    # ── Core Gate: Signal → Risk → Execution ──────────────────────────

    def validate_signal(
        self,
        signal: Dict,
        account_balance: Decimal,
        current_positions: List[Dict],
        current_prices: Dict[str, Decimal],
        daily_pnl: Decimal = Decimal('0'),
        peak_equity: Decimal = None,
        current_equity: Decimal = None,
    ) -> RiskDecision:
        """
        THE critical function. Every signal MUST pass through here.

        Args:
            signal: Signal dict with symbol, direction, entry_price, stop_loss, confidence
            account_balance: Current account balance
            current_positions: List of current open positions
            current_prices: Current market prices {symbol: price}
            daily_pnl: Today's realized PnL
            peak_equity: Highest equity reached (for drawdown calc)
            current_equity: Current portfolio equity

        Returns:
            RiskDecision with approval status and position sizing
        """
        symbol = signal.get('symbol', '')
        direction = signal.get('direction', '')
        entry_price = Decimal(str(signal.get('entry_price', 0)))
        stop_loss = Decimal(str(signal.get('stop_loss', 0)))
        confidence = signal.get('confidence', 50)

        # ── Step 1: Kill switch check ────────────────────────────────
        if self._kill_switch_active:
            return RiskDecision(
                approved=False,
                reason=f'Kill switch active: {self._kill_switch_reason}',
                kill_switch_active=True,
            )

        # ── Step 2: Validate signal inputs ───────────────────────────
        if entry_price <= 0:
            return RiskDecision(approved=False, reason='Invalid entry price')
        if stop_loss <= 0:
            return RiskDecision(approved=False, reason='Invalid stop loss')
        if direction not in ('buy', 'strong_buy', 'sell', 'strong_sell'):
            return RiskDecision(approved=False, reason=f'Invalid direction: {direction}')

        # ── Step 3: Maximum concurrent positions ─────────────────────
        active_count = sum(1 for p in current_positions if p.get('is_active', True))
        max_positions = self._get_param('max_concurrent_positions')
        if active_count >= max_positions:
            return RiskDecision(
                approved=False,
                reason=f'Max concurrent positions reached ({active_count}/{max_positions})',
            )

        # ── Step 4: Daily loss limit ─────────────────────────────────
        daily_loss_limit = self._get_param('daily_loss_limit_pct')
        if current_equity and current_equity > 0:
            daily_loss_pct = abs(daily_pnl) / current_equity * 100 if daily_pnl < 0 else Decimal('0')
            if daily_loss_pct >= daily_loss_limit:
                self._activate_kill_switch(f'Daily loss limit exceeded: {daily_loss_pct:.2f}% >= {daily_loss_limit}%')
                return RiskDecision(
                    approved=False,
                    reason=f'Daily loss limit exceeded: {daily_loss_pct:.2f}%',
                    kill_switch_active=True,
                )

        # ── Step 5: Drawdown limit ───────────────────────────────────
        if peak_equity and current_equity and peak_equity > 0:
            drawdown_pct = (peak_equity - current_equity) / peak_equity * 100
            max_dd = self._get_param('max_drawdown_pct')
            if drawdown_pct >= max_dd:
                self._activate_kill_switch(f'Max drawdown exceeded: {drawdown_pct:.2f}% >= {max_dd}%')
                return RiskDecision(
                    approved=False,
                    reason=f'Max drawdown exceeded: {drawdown_pct:.2f}%',
                    kill_switch_active=True,
                )

        # ── Step 6: Portfolio exposure limit ─────────────────────────
        total_exposure = sum(
            Decimal(str(p.get('quantity', 0))) * Decimal(str(p.get('current_price', 0)))
            for p in current_positions if p.get('is_active', True)
        )
        exposure_pct = (total_exposure / account_balance * 100) if account_balance > 0 else Decimal('0')
        max_exposure = self._get_param('max_portfolio_exposure_pct')
        if exposure_pct >= max_exposure:
            return RiskDecision(
                approved=False,
                reason=f'Portfolio exposure limit reached: {exposure_pct:.1f}% >= {max_exposure}%',
                risk_state={'exposure_pct': float(exposure_pct)},
            )

        # ── Step 7: Portfolio risk limit ─────────────────────────────
        total_risk = sum(
            Decimal(str(p.get('risk_amount', 0)))
            for p in current_positions if p.get('is_active', True)
        )
        risk_pct = (total_risk / account_balance * 100) if account_balance > 0 else Decimal('0')
        max_risk = self._get_param('max_portfolio_risk_pct')
        if risk_pct >= max_risk:
            return RiskDecision(
                approved=False,
                reason=f'Portfolio risk limit reached: {risk_pct:.1f}% >= {max_risk}%',
                risk_state={'risk_pct': float(risk_pct)},
            )

        # ── Step 8: Correlated positions ─────────────────────────────
        base_asset = symbol.split('/')[0] if '/' in symbol else symbol
        correlated_count = sum(
            1 for p in current_positions
            if p.get('is_active', True) and
            (p.get('symbol', '').split('/')[0] if '/' in p.get('symbol', '') else p.get('symbol', '')) == base_asset
        )
        max_correlated = self._get_param('max_correlated_positions')
        if correlated_count >= max_correlated:
            return RiskDecision(
                approved=False,
                reason=f'Max correlated positions for {base_asset}: {correlated_count}/{max_correlated}',
            )

        # ── Step 9: Calculate position size ──────────────────────────
        position_size, risk_amount, risk_percent = self._calculate_position_size(
            account_balance=account_balance,
            entry_price=entry_price,
            stop_loss=stop_loss,
            confidence=confidence,
            direction=direction,
        )

        # ── Step 10: Check position size against limits ──────────────
        max_position_pct = self._get_param('max_position_size_pct')
        position_value = Decimal(str(position_size)) * entry_price
        max_value = account_balance * (max_position_pct / 100)

        adjusted = False
        if position_value > max_value:
            position_size = float(max_value / entry_price)
            position_value = max_value
            adjusted = True

        # Check risk per trade limit
        max_risk_per_trade = self._get_param('max_risk_per_trade')
        if risk_percent > max_risk_per_trade:
            # Scale down position to meet risk limit
            scale = max_risk_per_trade / risk_percent
            position_size = float(Decimal(str(position_size)) * scale)
            risk_amount = float(Decimal(str(risk_amount)) * scale)
            risk_percent = float(max_risk_per_trade)
            adjusted = True

        return RiskDecision(
            approved=True,
            modified=adjusted,
            reason='Approved' + (' (position resized)' if adjusted else ''),
            position_size=position_size,
            risk_amount=risk_amount,
            risk_percent=risk_percent,
            adjusted_size=position_size if adjusted else None,
            risk_state={
                'exposure_pct': float(exposure_pct),
                'risk_pct': float(risk_pct),
                'active_positions': active_count,
                'correlated_count': correlated_count,
            },
        )

    # ── Kill Switch ───────────────────────────────────────────────────

    def _activate_kill_switch(self, reason: str):
        """Activate kill switch — blocks ALL new trades."""
        self._kill_switch_active = True
        self._kill_switch_reason = reason
        logger.critical(f"KILL SWITCH ACTIVATED: {reason}")

    def activate_kill_switch(self, reason: str):
        """Public method to activate kill switch."""
        self._activate_kill_switch(reason)

    def deactivate_kill_switch(self, reason: str = 'Manual deactivation'):
        """Deactivate kill switch — requires explicit action."""
        self._kill_switch_active = False
        self._kill_switch_reason = ''
        logger.info(f"Kill switch deactivated: {reason}")

    def is_kill_switch_active(self) -> bool:
        """Check if kill switch is active."""
        return self._kill_switch_active

    def check_kill_switch_triggers(
        self,
        account_balance: Decimal,
        current_equity: Decimal,
        peak_equity: Decimal,
        daily_pnl: Decimal,
        data_feeds_healthy: bool = True,
        api_healthy: bool = True,
        volatility_level: str = 'normal',
    ) -> Tuple[bool, str]:
        """
        Check all kill switch triggers.

        Returns:
            Tuple of (should_activate, reason)
        """
        if self.config and not getattr(self.config, 'kill_switch_enabled', True):
            return False, ''

        # Drawdown check
        if getattr(self.config, 'kill_on_drawdown', True) and peak_equity > 0:
            drawdown = (peak_equity - current_equity) / peak_equity * 100
            max_dd = self._get_param('max_drawdown_pct')
            if drawdown >= max_dd:
                return True, f'Drawdown {drawdown:.2f}% exceeds limit {max_dd}%'

        # Daily loss check
        if getattr(self.config, 'kill_on_daily_loss', True) and current_equity > 0:
            daily_loss = abs(daily_pnl) / current_equity * 100 if daily_pnl < 0 else Decimal('0')
            daily_limit = self._get_param('daily_loss_limit_pct')
            if daily_loss >= daily_limit:
                return True, f'Daily loss {daily_loss:.2f}% exceeds limit {daily_limit}%'

        # Data feed check
        if getattr(self.config, 'kill_on_data_feed_failure', True) and not data_feeds_healthy:
            return True, 'Data feed failure detected'

        # API check
        if getattr(self.config, 'kill_on_api_failure', True) and not api_healthy:
            return True, 'Exchange API failure detected'

        # Volatility check
        if getattr(self.config, 'kill_on_extreme_volatility', True) and volatility_level == 'extreme':
            return True, 'Extreme volatility detected'

        return False, ''

    # ── Position Sizing ───────────────────────────────────────────────

    def _calculate_position_size(
        self,
        account_balance: Decimal,
        entry_price: Decimal,
        stop_loss: Decimal,
        confidence: int,
        direction: str,
    ) -> Tuple[float, float, float]:
        """
        Calculate position size based on risk budgets.

        Returns:
            Tuple of (position_size, risk_amount, risk_percent)
        """
        risk_per_trade = self._get_param('max_risk_per_trade')

        # Risk per unit
        if direction in ('buy', 'strong_buy'):
            risk_per_unit = entry_price - stop_loss
        else:
            risk_per_unit = stop_loss - entry_price

        if risk_per_unit <= 0:
            return 0.0, 0.0, 0.0

        # Risk amount = account * risk_per_trade%
        risk_amount = account_balance * (risk_per_trade / 100)

        # Position size = risk_amount / risk_per_unit
        position_size = risk_amount / risk_per_unit

        # Adjust for confidence (50-100% range)
        confidence_factor = Decimal(str(max(50, min(100, confidence)))) / 100
        adjusted_size = position_size * (Decimal('0.5') + (confidence_factor * Decimal('0.5')))

        # Calculate final risk
        final_risk = adjusted_size * risk_per_unit
        risk_percent = (final_risk / account_balance * 100) if account_balance > 0 else Decimal('0')

        return float(adjusted_size), float(final_risk), float(risk_percent)

    # ── Portfolio Assessment ──────────────────────────────────────────

    def get_portfolio_risk_state(
        self,
        account_balance: Decimal,
        current_positions: List[Dict],
        peak_equity: Decimal = None,
        current_equity: Decimal = None,
        daily_pnl: Decimal = Decimal('0'),
    ) -> Dict:
        """
        Get comprehensive portfolio risk state.
        Used by dashboard and monitoring.
        """
        active = [p for p in current_positions if p.get('is_active', True)]

        total_exposure = sum(
            Decimal(str(p.get('quantity', 0))) * Decimal(str(p.get('current_price', 0)))
            for p in active
        )
        total_risk = sum(
            Decimal(str(p.get('risk_amount', 0)))
            for p in active
        )

        exposure_pct = (total_exposure / account_balance * 100) if account_balance > 0 else Decimal('0')
        risk_pct = (total_risk / account_balance * 100) if account_balance > 0 else Decimal('0')

        # Drawdown
        drawdown_pct = Decimal('0')
        if peak_equity and current_equity and peak_equity > 0:
            drawdown_pct = (peak_equity - current_equity) / peak_equity * 100

        # Daily PnL
        daily_pnl_pct = Decimal('0')
        if current_equity and current_equity > 0:
            daily_pnl_pct = (daily_pnl / current_equity * 100) if daily_pnl != 0 else Decimal('0')

        # Correlated groups
        correlated_groups = {}
        for p in active:
            base = p.get('symbol', '').split('/')[0] if '/' in p.get('symbol', '') else p.get('symbol', '')
            correlated_groups.setdefault(base, []).append(p)

        return {
            'kill_switch_active': self._kill_switch_active,
            'kill_switch_reason': self._kill_switch_reason,
            'position_count': len(active),
            'max_positions': self._get_param('max_concurrent_positions'),
            'total_exposure': float(total_exposure),
            'exposure_percent': float(exposure_pct),
            'max_exposure_percent': float(self._get_param('max_portfolio_exposure_pct')),
            'total_risk': float(total_risk),
            'risk_percent': float(risk_pct),
            'max_risk_percent': float(self._get_param('max_portfolio_risk_pct')),
            'drawdown_percent': float(drawdown_pct),
            'max_drawdown_percent': float(self._get_param('max_drawdown_pct')),
            'daily_pnl': float(daily_pnl),
            'daily_pnl_percent': float(daily_pnl_pct),
            'daily_loss_limit_percent': float(self._get_param('daily_loss_limit_pct')),
            'correlated_groups': {k: len(v) for k, v in correlated_groups.items()},
            'account_balance': float(account_balance),
            'limits': {
                'max_risk_per_trade': float(self._get_param('max_risk_per_trade')),
                'max_position_size_pct': float(self._get_param('max_position_size_pct')),
                'max_concurrent_positions': self._get_param('max_concurrent_positions'),
                'max_correlated_positions': self._get_param('max_correlated_positions'),
            },
        }

    # ── Helpers ───────────────────────────────────────────────────────

    def _get_param(self, name: str) -> Decimal:
        """Get parameter from config or default."""
        if self.config:
            val = getattr(self.config, name, None)
            if val is not None:
                return Decimal(str(val))
        return self.defaults.get(name, Decimal('0'))
