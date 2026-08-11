"""Signal Backtester - Historical strategy validation and performance analysis."""
import logging
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


class SignalBacktester:
    """
    Backtesting engine for validating signal generation strategies
    against historical data.
    """
    
    def __init__(self, initial_capital: Decimal = Decimal('10000')):
        self.initial_capital = initial_capital
        self.risk_per_trade = Decimal('1.0')  # 1% risk per trade
    
    def run_backtest(
        self,
        strategy_name: str,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        historical_data: List[Dict] = None,
        signals: List[Dict] = None,
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
            
        Returns:
            Dict with backtest results and metrics
        """
        # Generate synthetic data if not provided
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
        position = None
        peak_capital = capital
        max_drawdown = Decimal('0')
        
        for candle in historical_data:
            timestamp = candle.get('timestamp')
            close = Decimal(str(candle.get('close', 0)))
            
            # Check for entry signals
            entry_signal = self._find_entry_signal(signals, timestamp)
            if entry_signal and position is None:
                position = self._open_position(
                    entry_signal, close, capital
                )
            
            # Check for exit signals or stop loss
            if position:
                exit_signal = self._find_exit_signal(signals, timestamp)
                stop_hit = self._check_stop_loss(position, close)
                
                if exit_signal or stop_hit:
                    reason = 'stop_loss' if stop_hit else 'signal_exit'
                    trade = self._close_position(position, close, reason)
                    trades.append(trade)
                    capital += trade['pnl']
                    position = None
            
            # Track equity
            unrealized = self._calculate_unrealized_pnl(position, close) if position else Decimal('0')
            current_equity = capital + unrealized
            equity_curve.append({
                'timestamp': timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
                'equity': float(current_equity),
            })
            
            # Track drawdown
            if current_equity > peak_capital:
                peak_capital = current_equity
            drawdown = (peak_capital - current_equity) / peak_capital * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Close any remaining position
        if position and historical_data:
            last_close = Decimal(str(historical_data[-1].get('close', 0)))
            trade = self._close_position(position, last_close, 'backtest_end')
            trades.append(trade)
            capital += trade['pnl']
        
        # Calculate metrics
        metrics = self._calculate_metrics(trades, capital)
        metrics['max_drawdown'] = float(max_drawdown)
        metrics['equity_curve'] = equity_curve
        metrics['trades'] = trades
        
        result = {
            'strategy_name': strategy_name,
            'symbol': symbol,
            'timeframe': timeframe,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'initial_capital': float(self.initial_capital),
            'final_capital': float(capital),
            **metrics,
        }
        
        logger.info(
            f"Backtest complete: {strategy_name} on {symbol} - "
            f"Return: {metrics['total_return_percent']:.2f}%"
        )
        return result
    
    def _generate_synthetic_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str,
    ) -> List[Dict]:
        """Generate synthetic OHLCV data for testing."""
        data = []
        current = start_date
        
        # Base price depends on symbol
        base_price = 50000 if 'BTC' in symbol else 3000 if 'ETH' in symbol else 100
        price = Decimal(str(base_price))
        
        # Timeframe multiplier
        tf_minutes = {
            '1m': 1, '5m': 5, '15m': 15, '30m': 30,
            '1h': 60, '4h': 240, '1d': 1440,
        }.get(timeframe, 60)
        
        while current < end_date:
            # Random price movement
            change_pct = Decimal(str(random.uniform(-0.03, 0.03)))
            open_price = price
            high = price * (1 + Decimal(str(random.uniform(0, 0.02))))
            low = price * (1 - Decimal(str(random.uniform(0, 0.02))))
            close = price * (1 + change_pct)
            
            data.append({
                'timestamp': current,
                'open': float(open_price),
                'high': float(max(high, open_price, close)),
                'low': float(min(low, open_price, close)),
                'close': float(close),
                'volume': random.uniform(100, 10000),
            })
            
            price = close
            current += timedelta(minutes=tf_minutes)
        
        return data
    
    def _generate_signals_from_data(self, data: List[Dict]) -> List[Dict]:
        """Generate simple signals from price data for testing."""
        signals = []
        
        for i in range(2, len(data)):
            close = Decimal(str(data[i]['close']))
            prev_close = Decimal(str(data[i - 1]['close']))
            prev_prev_close = Decimal(str(data[i - 2]['close']))
            
            # Simple moving average crossover
            if prev_close > prev_prev_close and close < prev_close:
                # Generate both entry and exit signals
                signals.append({
                    'timestamp': data[i]['timestamp'],
                    'direction': 'buy',
                    'price': float(close),
                })
                signals.append({
                    'timestamp': data[i]['timestamp'],
                    'direction': 'exit',
                    'price': float(close * Decimal('1.02')),  # 2% take profit
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
                    'price': float(close * Decimal('0.98')),  # 2% take profit
                })
        
        return signals
    
    def _find_entry_signal(self, signals: List[Dict], timestamp) -> Optional[Dict]:
        """Find an entry signal at or near a timestamp."""
        for signal in signals:
            if signal['timestamp'] == timestamp and signal['direction'] in ('buy', 'sell'):
                return signal
        return None
    
    def _find_exit_signal(self, signals: List[Dict], timestamp) -> Optional[Dict]:
        """Find an exit signal at a timestamp."""
        for signal in signals:
            if signal['timestamp'] == timestamp and signal['direction'] in ('exit', 'take_profit', 'stop_loss'):
                return signal
        return None
    
    def _open_position(self, signal: Dict, price: Decimal, capital: Decimal) -> Dict:
        """Open a backtest position."""
        risk_amount = capital * (self.risk_per_trade / 100)
        stop_distance = price * Decimal('0.02')  # 2% stop loss
        
        quantity = risk_amount / stop_distance
        
        return {
            'side': 'long' if signal['direction'] == 'buy' else 'short',
            'entry_price': float(price),
            'quantity': float(quantity),
            'stop_loss': float(price - stop_distance) if signal['direction'] == 'buy' else float(price + stop_distance),
            'entry_time': signal['timestamp'],
        }
    
    def _close_position(self, position: Dict, price: Decimal, reason: str) -> Dict:
        """Close a backtest position and calculate PnL."""
        entry_price = Decimal(str(position['entry_price']))
        quantity = Decimal(str(position['quantity']))
        side = position['side']
        
        if side == 'long':
            pnl = quantity * (price - entry_price)
        else:
            pnl = quantity * (entry_price - price)
        
        pnl_pct = (pnl / (quantity * entry_price) * 100) if entry_price > 0 else Decimal('0')
        
        return {
            'side': side,
            'entry_price': position['entry_price'],
            'exit_price': float(price),
            'quantity': position['quantity'],
            'pnl': float(pnl),
            'pnl_percent': float(pnl_pct),
            'entry_time': str(position['entry_time']),
            'exit_time': str(price),
            'reason': reason,
        }
    
    def _check_stop_loss(self, position: Dict, current_price: Decimal) -> bool:
        """Check if stop loss has been hit."""
        stop = Decimal(str(position['stop_loss']))
        side = position['side']
        
        if side == 'long' and current_price <= stop:
            return True
        elif side == 'short' and current_price >= stop:
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
    
    def _calculate_metrics(self, trades: List[Dict], final_capital: Decimal) -> Dict:
        """Calculate comprehensive backtest metrics."""
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
        
        # Calculate Sharpe ratio (simplified)
        import math
        returns = [Decimal(str(t['pnl_percent'])) for t in trades]
        avg_return = sum(returns) / len(returns) if returns else Decimal('0')
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns) if returns else Decimal('1')
        std_return = Decimal(str(math.sqrt(float(variance)))) if variance > 0 else Decimal('1')
        sharpe = (avg_return / std_return) if std_return > 0 else Decimal('0')
        
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
            'final_capital': float(final_capital),
        }
