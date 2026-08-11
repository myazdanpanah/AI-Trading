"""CoinGecko exchange adapter - free API, no keys needed."""
import aiohttp
import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from .base import BaseExchange, OHLCV, OrderBook, OrderBookLevel, FundingRate, OpenInterest

COINGECKO_BASE = "https://api.coingecko.com/api/v3"

# Map trading pair symbols to CoinGecko coin IDs
SYMBOL_TO_COINGECKO = {
    "BTCUSDT": "bitcoin",
    "ETHUSDT": "ethereum",
    "SOLUSDT": "solana",
    "BNBUSDT": "binancecoin",
    "XRPUSDT": "ripple",
    "ADAUSDT": "cardano",
    "DOGEUSDT": "dogecoin",
    "DOTUSDT": "polkadot",
    "AVAXUSDT": "avalanche-2",
    "LINKUSDT": "chainlink",
    "MATICUSDT": "matic-network",
    "UNIUSDT": "uniswap",
    "ATOMUSDT": "cosmos",
    "LTCUSDT": "litecoin",
    "FILUSDT": "filecoin",
}

# CoinGecko OHLC days mapping
TIMEFRAME_TO_DAYS = {
    "1m": "1",
    "5m": "1",
    "15m": "1",
    "1h": "1",
    "4h": "7",
    "1d": "30",
    "1w": "90",
}


class CoinGeckoExchange(BaseExchange):
    """CoinGecko exchange adapter using their free public API."""

    def __init__(self, api_key: str = "", api_secret: str = "", **kwargs):
        super().__init__(api_key, api_secret)
        self.name = "coingecko"
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_request_time = 0
        self._min_interval = 1.5  # CoinGecko free tier: ~30 req/min

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={"Accept": "application/json"},
            )
        return self._session

    async def _throttled_get(self, url: str, params: dict = None) -> dict:
        """Make a rate-limited GET request."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        if elapsed < self._min_interval:
            await asyncio.sleep(self._min_interval - elapsed)

        session = await self._get_session()
        try:
            async with session.get(url, params=params) as resp:
                self._last_request_time = asyncio.get_event_loop().time()
                if resp.status == 429:
                    # Rate limited, wait and retry
                    await asyncio.sleep(60)
                    async with session.get(url, params=params) as retry_resp:
                        return await retry_resp.json()
                if resp.status != 200:
                    print(f"CoinGecko API error {resp.status}: {url}")
                    return {}
                return await resp.json()
        except Exception as e:
            print(f"CoinGecko request error: {e}")
            return {}

    def _get_coin_id(self, symbol: str) -> str:
        """Convert trading symbol to CoinGecko coin ID."""
        clean = symbol.upper().replace("/", "").replace("-", "")
        return SYMBOL_TO_COINGECKO.get(clean, "bitcoin")

    async def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> List[OHLCV]:
        """Fetch OHLCV candles from CoinGecko."""
        coin_id = self._get_coin_id(symbol)
        days = TIMEFRAME_TO_DAYS.get(timeframe, "1")

        data = await self._throttled_get(
            f"{COINGECKO_BASE}/coins/{coin_id}/ohlc",
            params={"vs_currency": "usd", "days": days},
        )

        if not data:
            return []

        candles = []
        for candle in data[-limit:]:
            candles.append(OHLCV(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=datetime.fromtimestamp(candle[0] / 1000),
                open=Decimal(str(candle[1])),
                high=Decimal(str(candle[2])),
                low=Decimal(str(candle[3])),
                close=Decimal(str(candle[4])),
                volume=Decimal("0"),  # CoinGecko OHLC doesn't include volume
            ))

        return candles

    async def fetch_ticker(self, symbol: str) -> Dict:
        """Fetch current ticker data."""
        coin_id = self._get_coin_id(symbol)

        data = await self._throttled_get(
            f"{COINGECKO_BASE}/coins/{coin_id}",
            params={
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "false",
                "developer_data": "false",
            },
        )

        if not data or "market_data" not in data:
            return {}

        md = data["market_data"]
        return {
            "symbol": symbol,
            "last": md.get("current_price", {}).get("usd"),
            "bid": None,
            "ask": None,
            "high": md.get("high_24h", {}).get("usd"),
            "low": md.get("low_24h", {}).get("usd"),
            "volume": md.get("total_volume", {}).get("usd"),
            "percentage": md.get("price_change_percentage_24h"),
        }

    async def fetch_order_book(self, symbol: str, limit: int = 20) -> OrderBook:
        """CoinGecko doesn't provide order book data. Return empty."""
        return OrderBook(symbol=symbol, bids=[], asks=[], timestamp=datetime.now())

    async def fetch_funding_rate(self, symbol: str) -> FundingRate:
        """CoinGecko doesn't provide funding rates. Return zero."""
        return FundingRate(symbol=symbol, rate=Decimal("0"), timestamp=datetime.now())

    async def fetch_open_interest(self, symbol: str) -> OpenInterest:
        """CoinGecko doesn't provide open interest. Return zero."""
        return OpenInterest(symbol=symbol, amount=Decimal("0"), value=Decimal("0"), timestamp=datetime.now())

    async def fetch_market_data(self) -> Dict:
        """Fetch all market data at once (efficient single call)."""
        ids = list(SYMBOL_TO_COINGECKO.values())[:15]

        data = await self._throttled_get(
            f"{COINGECKO_BASE}/coins/markets",
            params={
                "vs_currency": "usd",
                "ids": ",".join(ids),
                "order": "market_cap_desc",
                "per_page": "15",
                "sparkline": "false",
            },
        )

        if not data:
            return {}

        # Build a reverse map: coin_id -> symbol
        id_to_symbol = {v: k for k, v in SYMBOL_TO_COINGECKO.items()}

        result = {}
        for coin in data:
            coin_id = coin["id"]
            symbol = id_to_symbol.get(coin_id, coin["symbol"].upper() + "USDT")
            result[symbol] = {
                "symbol": symbol,
                "price": coin.get("current_price"),
                "change_24h": coin.get("price_change_percentage_24h"),
                "volume": coin.get("total_volume"),
                "market_cap": coin.get("market_cap"),
                "high_24h": coin.get("high_24h"),
                "low_24h": coin.get("low_24h"),
            }

        return result

    async def fetch_all_tickers(self) -> Dict:
        """Fetch all tickers via market data endpoint."""
        return await self.fetch_market_data()

    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
