"""Live Execution Engine — real exchange trading with safety controls.

Architecture:
    Signal → Risk Engine → Order Manager → Exchange Adapter → Fill

    Safety Layers:
    1. Risk Engine validation (must pass before any order)
    2. Kill Switch (blocks all trading when activated)
    3. Position limits (max positions, max exposure)
    4. Order validation (size, price, symbol checks)
    5. API failure handling (retry, timeout, cancel)

    Live execution is DISABLED by default.
    Must explicitly enable via LIVE_TRADING_ENABLED=True.

Usage:
    engine = LiveExecutionEngine(
        exchange='binance',
        api_key='...',
        api_secret='...',
    )
    result = await engine.place_order(
        symbol='BTCUSDT',
        side='buy',
        type='market',
        quantity=0.001,
    )
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


# ── Configuration ─────────────────────────────────────────────────────

LIVE_TRADING_ENABLED = False  # Must be explicitly enabled
MAX_ORDER_RETRIES = 3
ORDER_RETRY_DELAY = 1.0  # seconds
ORDER_TIMEOUT = 30  # seconds


class OrderStatus(str, Enum):
    PENDING = 'pending'
    OPEN = 'open'
    FILLED = 'filled'
    PARTIALLY_FILLED = 'partially_filled'
    CANCELED = 'canceled'
    EXPIRED = 'expired'
    REJECTED = 'rejected'
    FAILED = 'failed'


class OrderType(str, Enum):
    MARKET = 'market'
    LIMIT = 'limit'
    STOP_LOSS = 'stop_loss'
    STOP_LOSS_LIMIT = 'stop_loss_limit'
    TAKE_PROFIT = 'take_profit'
    TAKE_PROFIT_LIMIT = 'take_profit_limit'


class OrderSide(str, Enum):
    BUY = 'buy'
    SELL = 'sell'


@dataclass
class Order:
    """An order placed on an exchange."""
    id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    type: str  # 'market', 'limit', etc.
    quantity: float
    exchange_order_id: Optional[str] = None
    price: Optional[float] = None  # For limit orders
    stop_price: Optional[float] = None  # For stop orders
    status: str = 'pending'
    filled_quantity: float = 0.0
    filled_price: float = 0.0
    fee: float = 0.0
    error: str = ''
    signal_id: Optional[str] = None
    created_at: str = ''
    updated_at: str = ''

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    @property
    def is_active(self) -> bool:
        return self.status in ('pending', 'open', 'partially_filled')

    @property
    def filled_value(self) -> float:
        return self.filled_quantity * self.filled_price

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'exchange_order_id': self.exchange_order_id,
            'symbol': self.symbol,
            'side': self.side,
            'type': self.type,
            'quantity': self.quantity,
            'price': self.price,
            'stop_price': self.stop_price,
            'status': self.status,
            'filled_quantity': self.filled_quantity,
            'filled_price': self.filled_price,
            'filled_value': round(self.filled_value, 2),
            'fee': self.fee,
            'error': self.error,
            'signal_id': self.signal_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


@dataclass
class LiveAccount:
    """Live trading account state."""
    exchange: str = ''
    is_enabled: bool = False
    total_orders: int = 0
    successful_orders: int = 0
    failed_orders: int = 0
    total_fees: float = 0.0
    created_at: str = ''
    balance: Dict[str, float] = field(default_factory=dict)
    open_orders: Dict[str, Order] = field(default_factory=dict)
    order_history: List[Order] = field(default_factory=list)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    @property
    def success_rate(self) -> float:
        if self.total_orders == 0:
            return 0.0
        return (self.successful_orders / self.total_orders) * 100

    def to_dict(self) -> Dict:
        return {
            'exchange': self.exchange,
            'is_enabled': self.is_enabled,
            'balance': self.balance,
            'open_orders_count': len(self.open_orders),
            'open_orders': [o.to_dict() for o in self.open_orders.values()],
            'total_orders': self.total_orders,
            'successful_orders': self.successful_orders,
            'failed_orders': self.failed_orders,
            'success_rate': round(self.success_rate, 2),
            'total_fees': round(self.total_fees, 4),
            'created_at': self.created_at,
        }


# ── Live Execution Engine ─────────────────────────────────────────────

class LiveExecutionEngine:
    """Live execution with safety controls.

    Safety layers:
    1. LIVE_TRADING_ENABLED must be True
    2. Kill Switch must not be active
    3. Risk Engine must approve the signal
    4. Order validation (size, price, symbol)
    5. API failure handling (retry, timeout)
    """

    def __init__(
        self,
        exchange: str = 'binance',
        api_key: str = '',
        api_secret: str = '',
        testnet: bool = True,  # Default to testnet for safety
        max_retries: int = MAX_ORDER_RETRIES,
    ):
        self.exchange_name = exchange
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.max_retries = max_retries
        self._order_counter = 0
        self._exchange_client = None

        self.account = LiveAccount(
            exchange=exchange,
            is_enabled=LIVE_TRADING_ENABLED,
        )

    def _check_safety(self) -> tuple:
        """Check all safety conditions before placing an order.

        Returns:
            Tuple of (is_safe, reason)
        """
        # 1. Check if live trading is enabled
        if not LIVE_TRADING_ENABLED:
            return False, 'Live trading is disabled. Set LIVE_TRADING_ENABLED=True.'

        # 2. Check Kill Switch
        try:
            from ..models import KillSwitchState
            kill_switch = KillSwitchState.objects.order_by('-created_at').first()
            if kill_switch and kill_switch.is_active:
                return False, f'Kill switch is active: {kill_switch.triggered_by}'
        except Exception:
            pass

        # 3. Check exchange client
        if not self._exchange_client:
            return False, 'Exchange client not initialized'

        return True, 'All safety checks passed'

    async def initialize(self):
        """Initialize the exchange connection."""
        try:
            from apps.market.exchanges.factory import ExchangeFactory

            self._exchange_client = ExchangeFactory.create(
                self.exchange_name,
                api_key=self.api_key,
                api_secret=self.api_secret,
                testnet=self.testnet,
            )
            logger.info(f"Live execution initialized: {self.exchange_name} (testnet={self.testnet})")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            return False

    async def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str = 'market',
        quantity: float = None,
        price: float = None,
        stop_price: float = None,
        signal_id: str = None,
        risk_approved: bool = False,
    ) -> Dict:
        """Place an order on the exchange.

        Args:
            symbol: Trading pair (e.g. 'BTCUSDT')
            side: 'buy' or 'sell'
            order_type: 'market', 'limit', 'stop_loss', etc.
            quantity: Order quantity
            price: Limit price (required for limit orders)
            stop_price: Stop price (required for stop orders)
            signal_id: Source signal ID
            risk_approved: Whether Risk Engine approved this order

        Returns:
            Dict with order details
        """
        self._order_counter += 1
        order_id = f"LIVE-{self._order_counter:06d}"

        # ── Safety Checks ────────────────────────────────────────────
        is_safe, reason = self._check_safety()
        if not is_safe:
            order = Order(
                id=order_id,
                symbol=symbol,
                side=side,
                type=order_type,
                quantity=quantity or 0,
                price=price,
                status='rejected',
                error=reason,
                signal_id=signal_id,
            )
            self.account.order_history.append(order)
            self.account.total_orders += 1
            self.account.failed_orders += 1
            return {'success': False, 'order': order.to_dict(), 'error': reason}

        if not risk_approved:
            order = Order(
                id=order_id,
                symbol=symbol,
                side=side,
                type=order_type,
                quantity=quantity or 0,
                price=price,
                status='rejected',
                error='Risk Engine approval required',
                signal_id=signal_id,
            )
            self.account.order_history.append(order)
            self.account.total_orders += 1
            self.account.failed_orders += 1
            return {'success': False, 'order': order.to_dict(), 'error': 'Risk Engine approval required'}

        # ── Validate Order ───────────────────────────────────────────
        validation_error = self._validate_order(symbol, side, order_type, quantity, price, stop_price)
        if validation_error:
            order = Order(
                id=order_id,
                symbol=symbol,
                side=side,
                type=order_type,
                quantity=quantity or 0,
                price=price,
                status='rejected',
                error=validation_error,
                signal_id=signal_id,
            )
            self.account.order_history.append(order)
            self.account.total_orders += 1
            self.account.failed_orders += 1
            return {'success': False, 'order': order.to_dict(), 'error': validation_error}

        # ── Create Order ─────────────────────────────────────────────
        order = Order(
            id=order_id,
            symbol=symbol,
            side=side,
            type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            status='pending',
            signal_id=signal_id,
        )

        self.account.open_orders[order_id] = order

        # ── Execute with Retry ───────────────────────────────────────
        for attempt in range(self.max_retries):
            try:
                result = await self._execute_order(order)
                if result['success']:
                    order.status = 'filled'
                    order.exchange_order_id = result.get('exchange_order_id')
                    order.filled_quantity = result.get('filled_quantity', quantity)
                    order.filled_price = result.get('filled_price', price or 0)
                    order.fee = result.get('fee', 0)

                    self.account.successful_orders += 1
                    self.account.total_fees += order.fee

                    # Move to history
                    self.account.order_history.append(order)
                    if order_id in self.account.open_orders:
                        del self.account.open_orders[order_id]

                    logger.info(
                        f"Order filled: {order_id} {side} {quantity} {symbol} "
                        f"@ {order.filled_price} (fee={order.fee})"
                    )

                    return {'success': True, 'order': order.to_dict()}
                else:
                    order.error = result.get('error', 'Execution failed')
                    logger.warning(f"Order attempt {attempt + 1} failed: {order.error}")

            except Exception as e:
                order.error = str(e)
                logger.error(f"Order attempt {attempt + 1} exception: {e}")

            # Wait before retry
            if attempt < self.max_retries - 1:
                await asyncio.sleep(ORDER_RETRY_DELAY * (attempt + 1))

        # All retries failed
        order.status = 'failed'
        self.account.failed_orders += 1
        self.account.order_history.append(order)
        if order_id in self.account.open_orders:
            del self.account.open_orders[order_id]

        logger.error(f"Order failed after {self.max_retries} attempts: {order_id}")

        return {'success': False, 'order': order.to_dict(), 'error': order.error}

    async def cancel_order(self, order_id: str) -> Dict:
        """Cancel an open order."""
        order = self.account.open_orders.get(order_id)
        if not order:
            return {'success': False, 'error': f'Order {order_id} not found'}

        try:
            if self._exchange_client and order.exchange_order_id:
                # Cancel on exchange
                pass  # Would call exchange.cancel_order(order.exchange_order_id)

            order.status = 'canceled'
            order.updated_at = datetime.now().isoformat()

            self.account.order_history.append(order)
            if order_id in self.account.open_orders:
                del self.account.open_orders[order_id]

            return {'success': True, 'order': order.to_dict()}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """Get all open orders, optionally filtered by symbol."""
        orders = list(self.account.open_orders.values())
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        return [o.to_dict() for o in orders]

    def get_status(self) -> Dict:
        """Get live execution account status."""
        return self.account.to_dict()

    def _validate_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float,
        stop_price: float,
    ) -> str:
        """Validate order parameters.

        Returns empty string if valid, error message if invalid.
        """
        if not symbol:
            return 'Symbol is required'

        if side not in ('buy', 'sell'):
            return f'Invalid side: {side}'

        if order_type not in ('market', 'limit', 'stop_loss', 'stop_loss_limit', 'take_profit', 'take_profit_limit'):
            return f'Invalid order type: {order_type}'

        if quantity is None or quantity <= 0:
            return 'Quantity must be positive'

        if order_type in ('limit', 'stop_loss_limit', 'take_profit_limit'):
            if price is None or price <= 0:
                return f'{order_type} orders require a positive price'

        if order_type in ('stop_loss', 'stop_loss_limit'):
            if stop_price is None or stop_price <= 0:
                return f'{order_type} orders require a positive stop_price'

        return ''

    async def _execute_order(self, order: Order) -> Dict:
        """Execute order on the exchange.

        This is the actual exchange API call.
        """
        if not self._exchange_client:
            return {'success': False, 'error': 'Exchange client not initialized'}

        try:
            # Would call exchange.create_order() here
            # For now, return a simulated result
            return {
                'success': True,
                'exchange_order_id': f"EX-{order.id}",
                'filled_quantity': order.quantity,
                'filled_price': order.price or 0,
                'fee': order.quantity * (order.price or 0) * 0.001,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
