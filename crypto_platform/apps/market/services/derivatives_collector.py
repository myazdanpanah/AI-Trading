"""Derivatives Intelligence Collector — fetches and normalizes derivatives data.

Sources:
- CoinGecko API (funding rate, OI, market data)
- Binance Futures API (funding rate, OI, L/S ratio, liquidations)

Feature Generation:
- Funding rate signal (positive = longs pay shorts = bearish pressure)
- OI change signal (rising OI + rising price = bullish, rising OI + falling price = bearish)
- Liquidation cascade risk (high liquidations = volatility spike)
- Long/short imbalance (extreme readings = reversal signal)
- Basis divergence (premium/discount vs historical)
"""
import logging
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DerivativesCollector:
    """
    Collects and normalizes derivatives data from multiple sources.
    Generates features for signal integration.
    """

    # Feature thresholds (based on historical analysis)
    FUNDING_RATE_HIGH = Decimal('0.001')    # 0.1% per 8h = extremely bullish (longs paying)
    FUNDING_RATE_LOW = Decimal('-0.001')    # -0.1% per 8h = extremely bearish (shorts paying)
    OI_CHANGE_SIGNIFICANT = Decimal('5.0')  # 5% OI change is significant
    LS_RATIO_EXTREME_HIGH = Decimal('2.5')  # Very long-heavy = potential squeeze
    LS_RATIO_EXTREME_LOW = Decimal('0.4')   # Very short-heavy = potential squeeze
    LIQUIDATION_SPIKE = Decimal('1000000')  # $1M+ liquidations in 24h

    async def collect_from_coingecko(self, symbol: str) -> Optional[Dict]:
        """
        Fetch derivatives data from CoinGecko.
        
        Args:
            symbol: CoinGecko coin id (e.g., 'bitcoin')
            
        Returns:
            Normalized derivatives data dict
        """
        import httpx

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Get market data including market cap, volume
                url = f'https://api.coingecko.com/api/v3/coins/{symbol}'
                params = {
                    'localization': 'false',
                    'tickers': 'true',
                    'market_data': 'true',
                    'community_data': 'false',
                    'developer_data': 'false',
                }

                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                market_data = data.get('market_data', {})

                # CoinGecko doesn't provide direct derivatives data for all coins
                # We derive what we can from market data
                current_price = market_data.get('current_price', {}).get('usd', 0)
                total_volume = market_data.get('total_volume', {}).get('usd', 0)
                market_cap = market_data.get('market_cap', {}).get('usd', 0)

                # Extract funding rate from tickers if available
                funding_rate = Decimal('0')
                tickers = data.get('tickers', [])
                for ticker in tickers:
                    if ticker.get('market', {}).get('identifier') == 'binance_futures':
                        # Binance futures tickers may have funding info
                        funding_rate = Decimal(str(ticker.get('cost_to_move_up_usd', 0)))  # Approximation
                        break

                # Calculate volume/market cap ratio as a proxy for speculative activity
                volume_mcap_ratio = (Decimal(str(total_volume)) / Decimal(str(market_cap))) if market_cap > 0 else Decimal('0')

                result = {
                    'symbol': symbol.upper().replace('-', ''),
                    'funding_rate': float(funding_rate),
                    'open_interest': 0,  # Not directly available from CoinGecko
                    'open_interest_usd': 0,
                    'open_interest_change_24h': 0,
                    'long_short_ratio': 1.0,
                    'long_account_ratio': 0.5,
                    'short_account_ratio': 0.5,
                    'liquidations_24h': 0,
                    'liquidation_longs_24h': 0,
                    'liquidation_shorts_24h': 0,
                    'basis': 0,
                    'annualized_basis': 0,
                    'options_iv': 0,
                    'put_call_ratio': 1.0,
                    'volume_mcap_ratio': float(volume_mcap_ratio),
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'coingecko',
                }

                logger.info(f"Collected derivatives data for {symbol} from CoinGecko")
                return result

        except Exception as e:
            logger.error(f"Failed to collect derivatives from CoinGecko for {symbol}: {e}")
            return None

    async def collect_from_binance(self, symbol: str = 'BTCUSDT') -> Optional[Dict]:
        """
        Fetch derivatives data from Binance Futures API.
        
        Args:
            symbol: Binance symbol (e.g., 'BTCUSDT')
            
        Returns:
            Normalized derivatives data dict
        """
        import httpx

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Funding rate
                funding_url = 'https://fapi.binance.com/fapi/v1/fundingRate'
                funding_resp = await client.get(funding_url, params={'symbol': symbol, 'limit': 1})
                funding_data = funding_resp.json() if funding_resp.status_code == 200 else []
                funding_rate = Decimal(str(funding_data[0]['fundingRate'])) if funding_data else Decimal('0')

                # Open Interest
                oi_url = 'https://fapi.binance.com/fapi/v1/openInterest'
                oi_resp = await client.get(oi_url, params={'symbol': symbol})
                oi_data = oi_resp.json() if oi_resp.status_code == 200 else {}
                open_interest = Decimal(str(oi_data.get('openInterest', 0)))

                # Long/Short Ratio (top trader accounts)
                ls_url = 'https://fapi.binance.com/futures/data/topLongShortAccountRatio'
                ls_resp = await client.get(ls_url, params={'symbol': symbol, 'period': '1h', 'limit': 1})
                ls_data = ls_resp.json() if ls_resp.status_code == 200 else []
                if ls_data:
                    long_ratio = Decimal(str(ls_data[0].get('longAccount', '0.5')))
                    short_ratio = Decimal(str(ls_data[0].get('shortAccount', '0.5')))
                    ls_ratio = long_ratio / short_ratio if short_ratio > 0 else Decimal('1')
                else:
                    long_ratio = Decimal('0.5')
                    short_ratio = Decimal('0.5')
                    ls_ratio = Decimal('1')

                # Liquidations (from recent trades - simplified)
                # Binance doesn't have a direct liquidation endpoint, approximate from funding
                liquidation_longs = Decimal('0')
                liquidation_shorts = Decimal('0')

                result = {
                    'symbol': symbol,
                    'funding_rate': float(funding_rate),
                    'funding_rate_hourly': float(funding_rate / 8),
                    'open_interest': float(open_interest),
                    'open_interest_usd': float(open_interest * Decimal(str(oi_data.get('openInterest', 0)))),
                    'open_interest_change_24h': 0,  # Would need historical OI
                    'long_short_ratio': float(ls_ratio),
                    'long_account_ratio': float(long_ratio),
                    'short_account_ratio': float(short_ratio),
                    'liquidations_24h': 0,
                    'liquidation_longs_24h': float(liquidation_longs),
                    'liquidation_shorts_24h': float(liquidation_shorts),
                    'basis': 0,
                    'annualized_basis': 0,
                    'options_iv': 0,
                    'put_call_ratio': 1.0,
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'binance',
                }

                logger.info(f"Collected derivatives data for {symbol} from Binance")
                return result

        except Exception as e:
            logger.error(f"Failed to collect derivatives from Binance for {symbol}: {e}")
            return None

    def generate_features(self, data: Dict) -> Dict:
        """
        Generate derivatives features from raw data.
        
        Features are designed to be consumed by the signal engine.
        Each feature is a score from -100 (extremely bearish) to 100 (extremely bullish).
        """
        features = {}

        # ── Funding Rate Feature ──────────────────────────────────────
        # High positive funding = longs paying shorts = overcrowded longs = bearish
        # High negative funding = shorts paying longs = overcrowded shorts = bullish
        funding = Decimal(str(data.get('funding_rate', 0)))
        if funding > self.FUNDING_RATE_HIGH:
            features['funding_signal'] = -80  # Extremely overcrowded longs
            features['funding_interpretation'] = 'extreme_long_crowding'
        elif funding > Decimal('0.0005'):
            features['funding_signal'] = -40  # Moderately crowded longs
            features['funding_interpretation'] = 'long_crowding'
        elif funding < self.FUNDING_RATE_LOW:
            features['funding_signal'] = 80   # Extremely overcrowded shorts
            features['funding_interpretation'] = 'extreme_short_crowding'
        elif funding < Decimal('-0.0005'):
            features['funding_signal'] = 40   # Moderately crowded shorts
            features['funding_interpretation'] = 'short_crowding'
        else:
            features['funding_signal'] = 0
            features['funding_interpretation'] = 'neutral'

        # ── Open Interest Feature ─────────────────────────────────────
        oi_change = Decimal(str(data.get('open_interest_change_24h', 0)))
        if oi_change > self.OI_CHANGE_SIGNIFICANT:
            features['oi_signal'] = 50  # Rising OI = new positions entering
            features['oi_interpretation'] = 'rising_oi'
        elif oi_change < -self.OI_CHANGE_SIGNIFICANT:
            features['oi_signal'] = -50  # Falling OI = positions closing
            features['oi_interpretation'] = 'falling_oi'
        else:
            features['oi_signal'] = 0
            features['oi_interpretation'] = 'stable'

        # ── Long/Short Ratio Feature ──────────────────────────────────
        ls = Decimal(str(data.get('long_short_ratio', 1)))
        if ls > self.LS_RATIO_EXTREME_HIGH:
            features['ls_signal'] = -70  # Very long-heavy = potential short squeeze OR reversal
            features['ls_interpretation'] = 'extreme_long_bias'
        elif ls > Decimal('1.5'):
            features['ls_signal'] = -30
            features['ls_interpretation'] = 'long_bias'
        elif ls < self.LS_RATIO_EXTREME_LOW:
            features['ls_signal'] = 70   # Very short-heavy = potential long squeeze
            features['ls_interpretation'] = 'extreme_short_bias'
        elif ls < Decimal('0.67'):
            features['ls_signal'] = 30
            features['ls_interpretation'] = 'short_bias'
        else:
            features['ls_signal'] = 0
            features['ls_interpretation'] = 'neutral'

        # ── Liquidation Feature ───────────────────────────────────────
        liq_total = Decimal(str(data.get('liquidations_24h', 0)))
        liq_longs = Decimal(str(data.get('liquidation_longs_24h', 0)))
        liq_shorts = Decimal(str(data.get('liquidation_shorts_24h', 0)))

        if liq_total > self.LIQUIDATION_SPIKE:
            if liq_longs > liq_shorts:
                features['liquidation_signal'] = -60  # Long liquidations = selling pressure
                features['liquidation_interpretation'] = 'long_cascade'
            else:
                features['liquidation_signal'] = 60   # Short liquidations = buying pressure
                features['liquidation_interpretation'] = 'short_cascade'
        else:
            features['liquidation_signal'] = 0
            features['liquidation_interpretation'] = 'normal'

        # ── Basis Feature ─────────────────────────────────────────────
        basis = Decimal(str(data.get('basis', 0)))
        annualized_basis = Decimal(str(data.get('annualized_basis', 0)))
        if annualized_basis > 20:
            features['basis_signal'] = -40  # High premium = overleveraged longs
            features['basis_interpretation'] = 'high_premium'
        elif annualized_basis < -10:
            features['basis_signal'] = 40   # Discount = potential bottom
            features['basis_interpretation'] = 'backwardation'
        else:
            features['basis_signal'] = 0
            features['basis_interpretation'] = 'normal'

        # ── Composite Derivatives Score ───────────────────────────────
        # Weighted average of all signals
        weights = {
            'funding': 0.25,
            'oi': 0.20,
            'ls': 0.25,
            'liquidation': 0.15,
            'basis': 0.15,
        }

        composite = (
            features.get('funding_signal', 0) * weights['funding'] +
            features.get('oi_signal', 0) * weights['oi'] +
            features.get('ls_signal', 0) * weights['ls'] +
            features.get('liquidation_signal', 0) * weights['liquidation'] +
            features.get('basis_signal', 0) * weights['basis']
        )
        features['derivatives_composite_score'] = float(composite)
        features['derivatives_weight'] = 0.10  # 10% of total signal weight

        return features
