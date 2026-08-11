"""Arbitrage detection service - Cross-exchange opportunity finder."""
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class ArbitrageDetector:
    """Detects arbitrage opportunities across multiple exchanges."""
    
    # Fee structure per exchange (maker, taker)
    EXCHANGE_FEES = {
        'binance': (Decimal('0.001'), Decimal('0.001')),  # 0.1%
        'bybit': (Decimal('0.001'), Decimal('0.001')),    # 0.1%
        'okx': (Decimal('0.0008'), Decimal('0.001')),     # 0.08% / 0.1%
        'coinbase': (Decimal('0.004'), Decimal('0.006')), # 0.4% / 0.6%
    }
    
    def __init__(self, exchanges: List[str] = None):
        self.exchanges = exchanges or ['binance', 'bybit', 'okx']
    
    def find_opportunities(
        self,
        prices: Dict[str, Dict[str, Decimal]],
        min_spread_percent: Decimal = Decimal('0.5'),
        volume_threshold: Decimal = Decimal('1000'),
    ) -> List[Dict]:
        """
        Find arbitrage opportunities across exchanges.
        
        Args:
            prices: {exchange: {symbol: {bid, ask, volume}}}
            min_spread_percent: Minimum spread percentage to consider
            volume_threshold: Minimum volume in USD
            
        Returns:
            List of arbitrage opportunities
        """
        opportunities = []
        
        # Get all unique symbols
        all_symbols = set()
        for exchange_data in prices.values():
            all_symbols.update(exchange_data.keys())
        
        # Check each symbol across exchanges
        for symbol in all_symbols:
            exchange_prices = {}
            for exchange in self.exchanges:
                if exchange in prices and symbol in prices[exchange]:
                    exchange_prices[exchange] = prices[exchange][symbol]
            
            if len(exchange_prices) < 2:
                continue
            
            # Find best buy and sell prices
            best_buy_exchange = None
            best_buy_price = Decimal('Infinity')
            best_sell_exchange = None
            best_sell_price = Decimal('0')
            
            for exchange, data in exchange_prices.items():
                if data.get('ask') and data['ask'] < best_buy_price:
                    best_buy_price = data['ask']
                    best_buy_exchange = exchange
                if data.get('bid') and data['bid'] > best_sell_price:
                    best_sell_price = data['bid']
                    best_sell_exchange = exchange
            
            if not best_buy_exchange or not best_sell_exchange:
                continue
            if best_buy_exchange == best_sell_exchange:
                continue
            
            # Calculate spread
            if best_buy_price == 0:
                continue
                
            spread_percent = ((best_sell_price - best_buy_price) / best_buy_price) * 100
            
            if spread_percent < min_spread_percent:
                continue
            
            # Calculate fees
            buy_fee = self.EXCHANGE_FEES.get(best_buy_exchange, (Decimal('0.001'), Decimal('0.001')))[1]
            sell_fee = self.EXCHANGE_FEES.get(best_sell_exchange, (Decimal('0.001'), Decimal('0.001')))[1]
            total_fee = buy_fee + sell_fee
            
            # Calculate net profit
            net_profit_percent = spread_percent - (total_fee * 100)
            
            if net_profit_percent <= 0:
                continue
            
            # Get volume
            volume = min(
                exchange_prices[best_buy_exchange].get('volume', 0),
                exchange_prices[best_sell_exchange].get('volume', 0)
            )
            
            if volume < volume_threshold:
                continue
            
            opportunities.append({
                'symbol': symbol,
                'buy_exchange': best_buy_exchange,
                'sell_exchange': best_sell_exchange,
                'buy_price': best_buy_price,
                'sell_price': best_sell_price,
                'spread_percent': round(spread_percent, 4),
                'total_fee_percent': round(total_fee * 100, 4),
                'net_profit_percent': round(net_profit_percent, 4),
                'estimated_profit_usd': round(float((best_sell_price - best_buy_price) * min(volume, Decimal('10000'))), 2),
                'volume_available': float(volume),
                'risk_score': self._calculate_risk_score(spread_percent, volume, best_buy_exchange, best_sell_exchange),
                'detected_at': datetime.now().isoformat(),
            })
        
        # Sort by net profit
        opportunities.sort(key=lambda x: x['net_profit_percent'], reverse=True)
        
        logger.info(f"Found {len(opportunities)} arbitrage opportunities")
        return opportunities
    
    def _calculate_risk_score(
        self,
        spread: Decimal,
        volume: Decimal,
        exchange1: str,
        exchange2: str,
    ) -> int:
        """Calculate risk score for an arbitrage opportunity (0-100, lower is better)."""
        risk = 50
        
        # Higher spread = higher risk (may be manipulation)
        if spread > 5:
            risk += 20
        elif spread > 2:
            risk += 10
        elif spread < 1:
            risk -= 10
        
        # Lower volume = higher risk
        if volume < 5000:
            risk += 15
        elif volume < 10000:
            risk += 5
        elif volume > 100000:
            risk -= 10
        
        # Unknown exchanges = higher risk
        unknown_exchanges = {exchange1, exchange2} - set(self.EXCHANGE_FEES.keys())
        risk += len(unknown_exchanges) * 10
        
        return max(0, min(100, risk))
    
    def calculate_optimal_size(
        self,
        opportunity: Dict,
        max_position_usd: Decimal = Decimal('10000'),
    ) -> Decimal:
        """Calculate optimal position size for an arbitrage opportunity."""
        volume = Decimal(str(opportunity.get('volume_available', 0)))
        spread = Decimal(str(opportunity.get('spread_percent', 0)))
        
        # Conservative sizing based on spread and volume
        if spread > 2:
            size = min(volume * Decimal('0.1'), max_position_usd)
        elif spread > 1:
            size = min(volume * Decimal('0.05'), max_position_usd * Decimal('0.5'))
        else:
            size = min(volume * Decimal('0.02'), max_position_usd * Decimal('0.25'))
        
        return max(Decimal('100'), size)  # Minimum $100
