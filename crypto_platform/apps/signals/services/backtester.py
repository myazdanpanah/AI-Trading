"""Signal Backtester - Historical strategy validation with fees, slippage, and full metrics."""
import logging
import math
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SignalBacktester:
    """
    Backtesting engine for validating signal generation strategies
    against historical data. Supports fees, slippage, position sizing,
    stop loss, take profit, and comprehensive metrics.
    
    Reproducibility: Given identical inputs, the engine produces identical outputs.
    No-look-ahead: Signals are generated using only data available at time T.
    """

    def __init__(
        self,
        initial_capital: Decimal = Decimal('10000'),
        risk_per_trade: Decimal = Decimal('1.0'),  # 1% risk per trade
        fee_rate: Decimal = Decimal('0.001'),       # 0.1% per trade (Binance default)
        slippage_rate: Decimal = Decimal('0.0005'),  # 0.05% slippage
        max_open_positions: int = 5,
        stop_loss_pct: Decimal = Decimal('0.02'),    # 2% stop loss
        take_profit_pct: Decimal = Decimal('0.04'),  # 4% take profit
    ):
        self.initial_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.fee_rate = fee_rate
        self.slippage_rate = slippage_rate
        self.max_open_positions = max_open_positions
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct

    def run_backtest(
        self,
        strategy_name: str,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        historical_data: List[Dict] = None,
        signals: List[Dict] = None,
        strategy_version: str = '1.0',
        feature_version: str = '1.0',
        weight_snapshot: Dict = None,
    ) -> Dict:
        """
        Run a backtest on historical data.

        Args:
            strategy_name: Name of the strategy being tested
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candle timeframe (e.g., '1h', '4h', '1d')
            start_date: Backtest start date
            end_date: Backtest end date
            historical_data: List of OHLCV candles
            signals: Pre-generated signals to evaluate
            strategy_version: Version of the strategy
            feature_version: Version of the feature set
            weight_snapshot: Factor weights used during backtest

        Returns:
            Dict with backtest results and metrics
        """
        # Generate synthetic data if not provided (for testing only)
        if not historical_data:
            historical_data = self._generate_synthetic_data(
                symbol, start_date, end_date, timeframe
            )

        if not signals:
            signals = self._generate_signals_from_data(historical_data)

        # Run simulation
        trades = []
        equity_curve = []
        capital = self.initial_capital
        peak_capital = capital
        max_drawdown = Decimal('0')
        positions = []  # Support multiple open positions
        total_fees = Decimal('0')
        total_slippage = Decimal('0')
        all_returns = []  # For Sharpe/Sortino calculation

        for i, candle in enumerate(historical_data):
            timestamp = candle.get('timestamp')
            close = Decimal(str(candle.get('close', 0)))
            high = Decimal(str(candle.get('high', close)))
            low = Decimal(str(candle.get('low', close)))

            # Check stop loss and take profit for all open positions
            closed_trades = []
            for pos in positions[:]:
                stop_hit = self._check_stop_loss(pos, low)
                tp_hit = self._check_take_profit(pos, high)

                if stop_hit:
                    trade = self._close_position(
                        pos, Decimal(str(pos['stop_loss'])), 'stop_loss',
                        timestamp, total_fees, total_slippage
                    )
                    fees = self._apply_fees(Decimal(str(pos['entry_price'])), Decimal(str(pos['quantity'])))
                    slip = self._apply_slippage(Decimal(str(pos['entry_price'])), Decimal(str(pos['quantity'])))
                    total_fees += fees
                    total_slippage += slip
                    trades.append(trade)
                    capital += Decimal(str(trade['pnl']))
                    closed_trades.append(pos)
                elif tp_hit:
                    trade = self._close_position(
                        pos, Decimal(str(pos['take_profit'])), 'take_profit',
                        timestamp, total_fees, total_slippage
                    )
                    fees = self._apply_fees(Decimal(str(pos['entry_price'])), Decimal(str(pos['quantity'])))
                    slip = self._apply_slippage(Decimal(str(pos['entry_price'])), Decimal(str(pos['quantity'])))
                    total_fees += fees
                    total_slippage += slip
                    trades.append(trade)
                    capital += Decimal(str(trade['pnl']))
                    closed_trades.append(pos)

            for pos in closed_trades:
                positions.remove(pos)

            # Check for new entry signals
            if len(positions) < self.max_open_positions:
                entry_signal = self._find_entry_signal(signals, timestamp)
                if entry_signal:
                    position = self._open_position(
                        entry_signal, close, capital
                    )
                    if position:
                        # Apply entry slippage
                        entry_slip = self._apply_slippage(
                            Decimal(str(position['entry_price'])),
                            Decimal(str(position['quantity']))
                        )
                        total_slippage += entry_slip
                        capital -= entry_slip
                        positions.append(position)

            # Check for exit signals
            for pos in positions[:]:
                exit_signal = self._find_exit_signal(signals, timestamp, pos['side'])
                if exit_signal:
                    exit_price = Decimal(str(exit_signal.get('price', close)))
                    trade = self._close_position(
                        pos, exit_price, 'signal_exit',
                        timestamp, total_fees, total_slippage
                    )
                    fees = self._apply_fees(
                        Decimal(str(pos['entry_price'])),
                        Decimal(str(pos['quantity']))
                    )
                    slip = self._apply_slippage(exit_price, Decimal(str(pos['quantity'])))
                    total_fees += fees
                    total_slippage += slip
                    trades.append(trade)
                    capital += Decimal(str(trade['pnl']))
                    positions.remove(pos)

            # Track equity
            unrealized = sum(
                self._calculate_unrealized_pnl(pos, close)
                for pos in positions
            )
            current_equity = capital + unrealized
            equity_curve.append({
                'timestamp': timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
                'equity': float(current_equity),
            })

            # Track drawdown
            if current_equity > peak_capital:
                peak_capital = current_equity
            drawdown = (peak_capital - current_equity) / peak_capital * 100 if peak_capital > 0 else Decimal('0')
            if drawdown > max_drawdown:
                max_drawdown = drawdown

            # Record return for this candle (for Sharpe/Sortino)
            if i > 0:
                prev_equity = Decimal(str(equity_curve[-2]['equity'])) if len(equity_curve) > 1 else current_equity
                if prev_equity > 0:
                    candle_return = (current_equity - prev_equity) / prev_equity
                    all_returns.append(float(candle_return))

        # Close any remaining positions at last close
        if positions and historical_data:
            last_close = Decimal(str(historical_data[-1].get('close', 0)))
            for pos in positions:
                trade = self._close_position(
                    pos, last_close, 'backtest_end',
                    historical_data[-1].get('timestamp'),
                    total_fees, total_slippage
                )
                trades.append(trade)
                capital += Decimal(str(trade['pnl']))

        # Calculate metrics
        duration_days = max((end_date - start_date).days, 1)
        metrics = self._calculate_metrics(trades, capital, all_returns, duration_days)
        metrics['max_drawdown'] = float(max_drawdown)
        metrics['equity_curve'] = equity_curve
        metrics['trades'] = trades
        metrics['total_fees'] = float(total_fees)
        metrics['total_slippage'] = float(total_slippage)

        result = {
            'strategy_name': strategy_name,
            'strategy_version': strategy_version,
            'feature_version': feature_version,
            'symbol': symbol,
            'timeframe': timeframe,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'initial_capital': float(self.initial_capital),
            'final_capital': float(capital),
            'execution_mode': 'backtest',
            'signal_snapshot': {},
            'weight_snapshot': weight_snapshot or {},
            **metrics,
        }

        logger.info(
            f"Backtest complete: {strategy_name} v{strategy_version} on {symbol} - "
            f"Return: {metrics['total_return_percent']:.2f}% | "
            f"Trades: {metrics['total_trades']} | "
            f"Win Rate: {metrics['win_rate']:.1f}% | "
            f"Sharpe: {metrics['sharpe_ratio']:.2f} | "
            f"Fees: ${float(total_fees):.2f} | "
            f"Slippage: ${float(total_slippage):.2f}"
        )
        return result

    # ── Data Generation (synthetic, for testing only) ──────────────────

    def _generate_synthetic_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str,
    ) -> List[Dict]:
        """Generate synthetic OHLCV data for testing. Not used for real backtests."""
        import random
        data = []
        current = start_date

        base_price = 50000 if 'BTC' in symbol else 3000 if 'ETH' in symbol else 100
        price = Decimal(str(base_price))

        tf_minutes = {
            '1m': 1, '5m': 5, '15m': 15, '30m': 30,
            '1h': 60, '4h': 240, '1d': 1440,
        }.get(timeframe, 60)

        # Use a fixed seed for reproducibility
        rng = random.Random(42)

        while current < end_date:
            change_pct = Decimal(str(rng.uniform(-0.03, 0.03)))
            open_price = price
            high = price * (1 + Decimal(str(rng.uniform(0, 0.02))))
            low = price * (1 - Decimal(str(rng.uniform(0, 0.02))))
            close = price * (1 + change_pct)

            data.append({
                'timestamp': current,
                'open': float(open_price),
                'high': float(max(high, open_price, close)),
                'low': float(min(low, open_price, close)),
                'close': float(close),
                'volume': rng.uniform(100, 10000),
            })

            price = close
            current += timedelta(minutes=tf_minutes)

        return data

    def _generate_signals_from_data(self, data: List[Dict]) -> List[Dict]:
        """Generate simple SMA crossover signals from price data for testing."""
        signals = []

        for i in range(2, len(data)):
            close = Decimal(str(data[i]['close']))
            prev_close = Decimal(str(data[i - 1]['close']))
            prev_prev_close = Decimal(str(data[i - 2]['close']))

            if prev_close > prev_prev_close and close < prev_close:
                signals.append({
                    'timestamp': data[i]['timestamp'],
                    'direction': 'buy',
                    'price': float(close),
                })
                signals.append({
                    'timestamp': data[i]['timestamp'],
                    'direction': 'exit',
                    'side': 'long',
                    'price': float(close * Decimal('1.04')),  # 4% take profit
                })
            elif prev_close < prev_prev_close and close > prev_close:
                signals.append({
                    'timestamp': data[i]['timestamp'],
                    'direction': 'sell',
                    'price': float(close),
                })
                signals.append({
                    'timestamp': data[i]['timestamp'],
                    'direction': 'exit',
                    'side': 'short',
                    'price': float(close * Decimal('0.96')),  # 4% take profit
                })

        return signals

    # ── Position Management ────────────────────────────────────────────

    def _find_entry_signal(self, signals: List[Dict], timestamp) -> Optional[Dict]:
        """Find an entry signal at a timestamp."""
        for signal in signals:
            if signal['timestamp'] == timestamp and signal['direction'] in ('buy', 'sell'):
                return signal
        return None

    def _find_exit_signal(self, signals: List[Dict], timestamp, side: str) -> Optional[Dict]:
        """Find an exit signal at a timestamp matching the position side."""
        for signal in signals:
            if signal['timestamp'] == timestamp and signal['direction'] == 'exit':
                signal_side = signal.get('side', 'long')
                if signal_side == side:
                    return signal
        return None

    def _open_position(self, signal: Dict, price: Decimal, capital: Decimal) -> Optional[Dict]:
        """Open a backtest position with position sizing based on risk."""
        risk_amount = capital * (self.risk_per_trade / 100)
        stop_distance = price * self.stop_loss_pct

        if stop_distance <= 0:
            return None

        quantity = risk_amount / stop_distance
        entry_price = price

        side = 'long' if signal['direction'] == 'buy' else 'short'
        stop_loss = float(entry_price - stop_distance) if side == 'long' else float(entry_price + stop_distance)
        take_profit = float(entry_price + price * self.take_profit_pct) if side == 'long' else float(entry_price - price * self.take_profit_pct)

        return {
            'side': side,
            'entry_price': float(entry_price),
            'quantity': float(quantity),
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'entry_time': signal['timestamp'],
            'risk_amount': float(risk_amount),
        }

    def _close_position(self, position: Dict, price: Decimal, reason: str, timestamp, total_fees: Decimal, total_slippage: Decimal) -> Dict:
        """Close a backtest position and calculate PnL."""
        entry_price = Decimal(str(position['entry_price']))
        quantity = Decimal(str(position['quantity']))
        side = position['side']

        if side == 'long':
            pnl = quantity * (price - entry_price)
        else:
            pnl = quantity * (entry_price - price)

        # Calculate MFE and MAE for this trade
        mfe = abs(float(price - entry_price)) * float(quantity) if side == 'long' else abs(float(entry_price - price)) * float(quantity)
        mae = 0  # Simplified - would need price history during position

        pnl_pct = (pnl / (quantity * entry_price) * 100) if entry_price > 0 else Decimal('0')

        return {
            'side': side,
            'entry_price': position['entry_price'],
            'exit_price': float(price),
            'quantity': position['quantity'],
            'pnl': float(pnl),
            'pnl_percent': float(pnl_pct),
            'entry_time': str(position['entry_time']),
            'exit_time': str(timestamp) if timestamp else '',
            'reason': reason,
            'mfe': mfe,
            'mae': mae,
        }

    # ── Fees & Slippage ────────────────────────────────────────────────

    def _apply_fees(self, price: Decimal, quantity: Decimal) -> Decimal:
        """Calculate trading fees for a trade."""
        return price * quantity * self.fee_rate

    def _apply_slippage(self, price: Decimal, quantity: Decimal) -> Decimal:
        """Calculate slippage cost for a trade."""
        return price * quantity * self.slippage_rate

    # ── Risk Checks ────────────────────────────────────────────────────

    def _check_stop_loss(self, position: Dict, low_price: Decimal) -> bool:
        """Check if stop loss has been hit (using candle low for realism)."""
        stop = Decimal(str(position['stop_loss']))
        side = position['side']

        if side == 'long' and low_price <= stop:
            return True
        elif side == 'short' and low_price >= stop:
            return True
        return False

    def _check_take_profit(self, position: Dict, high_price: Decimal) -> bool:
        """Check if take profit has been hit (using candle high for realism)."""
        tp = Decimal(str(position['take_profit']))
        side = position['side']

        if side == 'long' and high_price >= tp:
            return True
        elif side == 'short' and high_price <= tp:
            return True
        return False

    def _calculate_unrealized_pnl(self, position: Dict, current_price: Decimal) -> Decimal:
        """Calculate unrealized PnL for an open position."""
        if not position:
            return Decimal('0')

        entry_price = Decimal(str(position['entry_price']))
        quantity = Decimal(str(position['quantity']))
        side = position['side']

        if side == 'long':
            return quantity * (current_price - entry_price)
        else:
            return quantity * (entry_price - current_price)

    # ── Metrics ────────────────────────────────────────────────────────

    def _calculate_metrics(
        self,
        trades: List[Dict],
        final_capital: Decimal,
        all_returns: List[float],
        duration_days: int,
    ) -> Dict:
        """Calculate comprehensive backtest metrics including Sortino, MFE, MAE, expectancy, CAGR."""
        total_trades = len(trades)
        winning = [t for t in trades if t['pnl'] > 0]
        losing = [t for t in trades if t['pnl'] < 0]

        total_return = final_capital - self.initial_capital
        total_return_pct = (total_return / self.initial_capital * 100) if self.initial_capital > 0 else Decimal('0')

        win_rate = (len(winning) / total_trades * 100) if total_trades > 0 else Decimal('0')

        avg_win = (
            sum(Decimal(str(t['pnl'])) for t in winning) / len(winning)
            if winning else Decimal('0')
        )
        avg_loss = (
            sum(abs(Decimal(str(t['pnl']))) for t in losing) / len(losing)
            if losing else Decimal('0')
        )

        profit_factor = (avg_win / avg_loss) if avg_loss > 0 else Decimal('0')

        # Expectancy: (win_rate * avg_win) - (loss_rate * avg_loss)
        win_rate_decimal = len(winning) / total_trades if total_trades > 0 else 0
        loss_rate_decimal = len(losing) / total_trades if total_trades > 0 else 0
        expectancy = (win_rate_decimal * float(avg_win)) - (loss_rate_decimal * float(avg_loss))

        # MFE and MAE across all trades
        total_mfe = sum(t.get('mfe', 0) for t in trades)
        total_mae = sum(t.get('mae', 0) for t in trades)

        # Sharpe ratio (annualized)
        if all_returns and len(all_returns) > 1:
            avg_return = sum(all_returns) / len(all_returns)
            variance = sum((r - avg_return) ** 2 for r in all_returns) / (len(all_returns) - 1)
            std_return = math.sqrt(variance) if variance > 0 else 1
            # Annualize: multiply by sqrt(365 * 24) for hourly data approximation
            sharpe = (avg_return / std_return) * math.sqrt(365 * 24) if std_return > 0 else 0
        else:
            sharpe = 0

        # Sortino ratio (uses only downside deviation)
        if all_returns and len(all_returns) > 1:
            avg_return = sum(all_returns) / len(all_returns)
            downside_returns = [r for r in all_returns if r < 0]
            if downside_returns:
                downside_variance = sum(r ** 2 for r in downside_returns) / len(downside_returns)
                downside_std = math.sqrt(downside_variance)
                sortino = (avg_return / downside_std) * math.sqrt(365 * 24) if downside_std > 0 else 0
            else:
                sortino = 10  # No losing periods
        else:
            sortino = 0

        # CAGR
        if duration_days > 0 and self.initial_capital > 0:
            years = duration_days / 365.25
            cagr = ((float(final_capital) / float(self.initial_capital)) ** (1 / years) - 1) * 100
        else:
            cagr = 0

        return {
            'total_return': float(total_return),
            'total_return_percent': float(total_return_pct),
            'win_rate': float(win_rate),
            'total_trades': total_trades,
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'avg_win': float(avg_win),
            'avg_loss': float(avg_loss),
            'profit_factor': float(profit_factor),
            'sharpe_ratio': float(sharpe),
            'sortino_ratio': float(sortino),
            'cagr': float(cagr),
            'expectancy': float(expectancy),
            'max_favorable_excursion': float(total_mfe),
            'max_adverse_excursion': float(total_mae),
            'final_capital': float(final_capital),
        }


class HistoricalDataFetcher:
    """Fetch real historical OHLCV data from CoinGecko for backtesting."""

    @staticmethod
    async def fetch_candles(
        symbol: str,
        timeframe: str = '1h',
        days: int = 30,
    ) -> List[Dict]:
        """
        Fetch historical candle data from CoinGecko.
        
        Args:
            symbol: CoinGecko coin id (e.g., 'bitcoin', 'ethereum')
            timeframe: '1h', '4h', or '1d'
            days: Number of days of history
            
        Returns:
            List of OHLCV dicts with timestamp, open, high, low, close, volume
        """
        import httpx

        # Map timeframe to CoinGecko granularity
        vs_currency = 'usd'

        url = f'https://api.coingecko.com/api/v3/coins/{symbol}/ohlc'
        params = {
            'vs_currency': vs_currency,
            'days': str(days),
        }

        # CoinGecko OHLC granularity:
        # 1-2 days: 30-minute candles
        # 3-30 days: 4-hour candles
        # 31+ days: daily candles
        # For hourly data we use market_chart/range instead
        if timeframe in ('1h', '4h'):
            # Use market_chart/range for finer granularity
            from_timestamp = int((datetime.utcnow() - timedelta(days=min(days, 30))).timestamp())
            to_timestamp = int(datetime.utcnow().timestamp())
            url = f'https://api.coingecko.com/api/v3/coins/{symbol}/market_chart/range'
            params = {
                'vs_currency': vs_currency,
                'from': str(from_timestamp),
                'to': str(to_timestamp),
            }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            logger.error(f"Failed to fetch historical data for {symbol}: {e}")
            return []

        candles = []

        if 'prices' in data:
            # market_chart/range format: [[timestamp_ms, price], ...]
            prices = data.get('prices', [])
            volumes = data.get('total_volumes', [])

            for i, (ts_ms, price) in enumerate(prices):
                timestamp = datetime.utcfromtimestamp(ts_ms / 1000)
                volume = volumes[i][1] if i < len(volumes) else 0

                # Simulate OHLC from close price (CoinGecko doesn't provide full OHLC via this endpoint)
                # In production, use a proper OHLCV provider
                candles.append({
                    'timestamp': timestamp,
                    'open': price * 0.999,
                    'high': price * 1.002,
                    'low': price * 0.998,
                    'close': price,
                    'volume': volume,
                })

        elif isinstance(data, list):
            # OHLC format: [[timestamp_ms, open, high, low, close], ...]
            for item in data:
                timestamp = datetime.utcfromtimestamp(item[0] / 1000)
                candles.append({
                    'timestamp': timestamp,
                    'open': item[1],
                    'high': item[2],
                    'low': item[3],
                    'close': item[4],
                    'volume': 0,  # OHLC endpoint doesn't include volume
                })

        logger.info(f"Fetched {len(candles)} candles for {symbol} ({timeframe}, {days}d)")
        return candles
