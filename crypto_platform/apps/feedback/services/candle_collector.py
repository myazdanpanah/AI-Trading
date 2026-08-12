"""Collect candle data for AI training and store in database."""
import logging
import json
import urllib.request
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)

# CoinGecko coin ID mapping
SYMBOL_TO_COINGECKO = {
    'BTCUSDT': 'bitcoin', 'ETHUSDT': 'ethereum', 'SOLUSDT': 'solana',
    'BNBUSDT': 'binancecoin', 'XRPUSDT': 'ripple', 'ADAUSDT': 'cardano',
    'DOGEUSDT': 'dogecoin', 'AVAXUSDT': 'avalanche-2', 'DOTUSDT': 'polkadot',
    'LINKUSDT': 'chainlink', 'MATICUSDT': 'matic-network', 'UNIUSDT': 'uniswap',
    'LTCUSDT': 'litecoin', 'ATOMUSDT': 'cosmos', 'NEARUSDT': 'near',
}

TIMEFRAME_TO_DAYS = {
    '1m': '1', '5m': '1', '15m': '1',
    '1h': '7', '4h': '30', '1d': '90',
}


class CandleCollector:
    """Fetch candle data from CoinGecko API and store for training."""
    
    TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h', '1d']
    COINGECKO_BASE = 'https://api.coingecko.com/api/v3'
    
    def _get_coin_id(self, symbol: str) -> str:
        """Convert trading symbol to CoinGecko coin ID."""
        clean = symbol.upper().replace('/', '').replace('-', '')
        return SYMBOL_TO_COINGECKO.get(clean, 'bitcoin')
    
    def collect_candles(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> dict:
        """Fetch candles from CoinGecko and store in database."""
        from apps.feedback.models import CandleData
        from datetime import timezone as tz
        
        coin_id = self._get_coin_id(symbol)
        days = TIMEFRAME_TO_DAYS.get(timeframe, '7')
        
        try:
            url = f"{self.COINGECKO_BASE}/coins/{coin_id}/ohlc?vs_currency=usd&days={days}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req, timeout=15)
            raw_data = json.loads(response.read())
            
            candles = []
            for c in raw_data[-limit:]:
                timestamp = datetime.fromtimestamp(c[0] / 1000, tz=tz.utc)
                candles.append({
                    'timestamp': timestamp,
                    'open': Decimal(str(c[1])),
                    'high': Decimal(str(c[2])),
                    'low': Decimal(str(c[3])),
                    'close': Decimal(str(c[4])),
                    'volume': Decimal('0'),  # CoinGecko OHLC doesn't include volume
                })
            
            # Rate limit: wait between requests
            import time
            time.sleep(2)
            
            logger.info(f"Fetched {len(candles)} candles from CoinGecko for {symbol}")
            
        except Exception as e:
            logger.error(f"Failed to fetch candles from CoinGecko: {e}")
            return {'error': str(e), 'symbol': symbol}
        
        try:
            stored = 0
            for candle in candles:
                timestamp = candle['timestamp']
                open_price = candle['open']
                high_price = candle['high']
                low_price = candle['low']
                close_price = candle['close']
                volume = candle['volume']
                
                # Calculate price change
                if open_price > 0:
                    price_change = close_price - open_price
                    price_change_pct = (price_change / open_price) * 100
                else:
                    price_change = Decimal('0')
                    price_change_pct = Decimal('0')
                
                # Detect candle pattern
                pattern = self._detect_pattern(open_price, high_price, low_price, close_price)
                
                # Store candle
                candle_obj, created = CandleData.objects.update_or_create(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=timestamp,
                    defaults={
                        'open_price': open_price,
                        'high_price': high_price,
                        'low_price': low_price,
                        'close_price': close_price,
                        'volume': volume,
                        'price_change': price_change,
                        'price_change_pct': price_change_pct,
                        'pattern': pattern,
                        'source': 'coingecko',
                    }
                )
                if created:
                    stored += 1
            
            logger.info(f"Collected {stored} new candles for {symbol} {timeframe}")
            return {'stored': stored, 'total': len(candles), 'symbol': symbol, 'timeframe': timeframe}
            
        except Exception as e:
            logger.error(f"Failed to store candles for {symbol}: {e}")
            return {'error': str(e), 'symbol': symbol}
    
    def _detect_pattern(self, open_p, high, low, close) -> str:
        """Detect candlestick pattern."""
        body = abs(close - open_p)
        total_range = high - low if high > low else Decimal('0.01')
        upper_shadow = high - max(open_p, close)
        lower_shadow = min(open_p, close) - low
        
        # Doji
        if body < total_range * Decimal('0.1'):
            return 'doji'
        
        # Hammer (bullish)
        if lower_shadow > body * Decimal('2') and upper_shadow < body * Decimal('0.3'):
            return 'hammer'
        
        # Shooting star (bearish)
        if upper_shadow > body * Decimal('2') and lower_shadow < body * Decimal('0.3'):
            return 'shooting_star'
        
        # Engulfing
        if close > open_p:
            return 'bullish_candle'
        else:
            return 'bearish_candle'
    
    def get_candles_for_training(self, symbol: str, timeframe: str = '1h', limit: int = 50) -> list:
        """Get recent candles formatted for AI training."""
        from apps.feedback.models import CandleData
        
        candles = CandleData.objects.filter(
            symbol=symbol,
            timeframe=timeframe
        ).order_by('-timestamp')[:limit]
        
        return [
            {
                'timestamp': c.timestamp.isoformat(),
                'open': float(c.open_price),
                'high': float(c.high_price),
                'low': float(c.low_price),
                'close': float(c.close_price),
                'volume': float(c.volume),
                'change_pct': float(c.price_change_pct),
                'pattern': c.pattern,
                'indicators': c.indicators or {},
            }
            for c in reversed(list(candles))
        ]
    
    def create_training_sample(self, signal_memory) -> dict:
        """Create a training sample from a signal memory with candle context."""
        from apps.feedback.models import TrainingSample, CandleData
        
        # Get candles around signal creation time
        signal_time = signal_memory.created_at
        symbol = signal_memory.signal.symbol if signal_memory.signal else 'BTCUSDT'
        timeframe = signal_memory.signal.timeframe if signal_memory.signal else '1h'
        
        # Get candle at signal creation
        candle_at_signal = CandleData.objects.filter(
            symbol=symbol,
            timeframe=timeframe,
            timestamp__lte=signal_time
        ).order_by('-timestamp').first()
        
        # Get next N candles after signal (for outcome context)
        next_candles = CandleData.objects.filter(
            symbol=symbol,
            timeframe=timeframe,
            timestamp__gt=signal_time
        ).order_by('timestamp')[:10]
        
        # Build input features
        input_features = {
            'symbol': symbol,
            'timeframe': timeframe,
            'signal_direction': signal_memory.signal_direction,
            'signal_confidence': signal_memory.signal_confidence,
            'entry_price': float(signal_memory.entry_price),
            'factors': signal_memory.factors_at_creation or {},
        }
        
        if candle_at_signal:
            input_features['candle'] = {
                'open': float(candle_at_signal.open_price),
                'high': float(candle_at_signal.high_price),
                'low': float(candle_at_signal.low_price),
                'close': float(candle_at_signal.close_price),
                'volume': float(candle_at_signal.volume),
                'pattern': candle_at_signal.pattern,
            }
        
        # Store training sample
        training_sample = TrainingSample.objects.create(
            signal_memory=signal_memory,
            candle_data=candle_at_signal,
            input_features=input_features,
            actual_outcome=signal_memory.signal_direction,
            actual_return=signal_memory.actual_return or Decimal('0'),
            candle_open=candle_at_signal.open_price if candle_at_signal else 0,
            candle_high=candle_at_signal.high_price if candle_at_signal else 0,
            candle_low=candle_at_signal.low_price if candle_at_signal else 0,
            candle_close=candle_at_signal.close_price if candle_at_signal else 0,
            candle_volume=candle_at_signal.volume if candle_at_signal else 0,
            next_candles=[
                {
                    'open': float(c.open_price),
                    'high': float(c.high_price),
                    'low': float(c.low_price),
                    'close': float(c.close_price),
                    'volume': float(c.volume),
                    'change_pct': float(c.price_change_pct),
                    'pattern': c.pattern,
                }
                for c in next_candles
            ],
            was_correct=signal_memory.was_correct,
        )
        
        return {
            'training_sample_id': str(training_sample.id),
            'symbol': symbol,
            'was_correct': training_sample.was_correct,
            'candles_included': len(next_candles) + (1 if candle_at_signal else 0),
        }


# Singleton
candle_collector = CandleCollector()
