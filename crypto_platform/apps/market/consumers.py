"""WebSocket consumers for live market data."""
import json
import asyncio
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)

# Global connection manager
connected_clients = set()
price_subscriptions = {}  # symbol -> set of consumers


class PriceFeedConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer that streams live prices from CoinGecko."""

    async def connect(self):
        self.symbol = self.scope['url_route']['kwargs'].get('symbol', 'BTC')
        self.room_name = f'prices_{self.symbol.upper()}'
        self.is_connected = True

        # Join price group
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        connected_clients.add(self)

        await self.accept()
        logger.info(f"WebSocket connected: {self.symbol} ({len(connected_clients)} total)")

        # Start price polling task
        self.price_task = asyncio.create_task(self._poll_prices())

    async def disconnect(self, close_code):
        self.is_connected = False
        connected_clients.discard(self)

        # Cancel polling
        if hasattr(self, 'price_task'):
            self.price_task.cancel()
            try:
                await self.price_task
            except asyncio.CancelledError:
                pass

        await self.channel_layer.group_discard(self.room_name, self.channel_name)
        logger.info(f"WebSocket disconnected: {self.symbol} ({len(connected_clients)} total)")

    async def receive(self, text_data):
        """Handle messages from client."""
        try:
            data = json.loads(text_data)
            action = data.get('action', '')

            if action == 'subscribe':
                # Subscribe to additional symbols
                symbols = data.get('symbols', [])
                for sym in symbols:
                    room = f'prices_{sym.upper()}'
                    await self.channel_layer.group_add(room, self.channel_name)
                    # Start polling for new symbol
                    asyncio.create_task(self._poll_symbol(sym))

            elif action == 'unsubscribe':
                symbols = data.get('symbols', [])
                for sym in symbols:
                    room = f'prices_{sym.upper()}'
                    await self.channel_layer.group_discard(room, self.channel_name)

            elif action == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))

        except json.JSONDecodeError:
            pass

    async def price_update(self, event):
        """Send price update to WebSocket client."""
        await self.send(text_data=json.dumps(event['data']))

    async def _poll_prices(self):
        """Poll CoinGecko for price updates."""
        import httpx

        symbol_map = {
            'BTC': 'bitcoin', 'ETH': 'ethereum', 'SOL': 'solana',
            'BNB': 'binancecoin', 'XRP': 'ripple', 'ADA': 'cardano',
            'DOGE': 'dogecoin', 'DOT': 'polkadot', 'AVAX': 'avalanche-2',
            'LINK': 'chainlink', 'MATIC': 'matic-network', 'SHIB': 'shiba-inu',
            'LTC': 'litecoin', 'UNI': 'uniswap', 'ATOM': 'cosmos',
        }

        coin_id = symbol_map.get(self.symbol.upper(), self.symbol.lower())

        async with httpx.AsyncClient(timeout=10.0) as client:
            while self.is_connected:
                try:
                    url = f'https://api.coingecko.com/api/v3/simple/price'
                    params = {
                        'ids': coin_id,
                        'vs_currencies': 'usd',
                        'include_24hr_change': 'true',
                        'include_24hr_vol': 'true',
                        'include_market_cap': 'true',
                    }
                    response = await client.get(url, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        if coin_id in data:
                            price_data = data[coin_id]
                            update = {
                                'type': 'price_update',
                                'symbol': self.symbol.upper(),
                                'price': price_data.get('usd', 0),
                                'change_24h': price_data.get('usd_24h_change', 0),
                                'volume_24h': price_data.get('usd_24h_vol', 0),
                                'market_cap': price_data.get('usd_market_cap', 0),
                            }
                            await self.send(text_data=json.dumps(update))

                    # Rate limit: update every 10 seconds
                    await asyncio.sleep(10)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.warning(f"Price poll error for {self.symbol}: {e}")
                    await asyncio.sleep(30)

    async def _poll_symbol(self, symbol):
        """Poll a specific symbol for price updates."""
        import httpx

        symbol_map = {
            'BTC': 'bitcoin', 'ETH': 'ethereum', 'SOL': 'solana',
            'BNB': 'binancecoin', 'XRP': 'ripple', 'ADA': 'cardano',
        }

        coin_id = symbol_map.get(symbol.upper(), symbol.lower())

        async with httpx.AsyncClient(timeout=10.0) as client:
            while self.is_connected:
                try:
                    url = f'https://api.coingecko.com/api/v3/simple/price'
                    params = {
                        'ids': coin_id,
                        'vs_currencies': 'usd',
                        'include_24hr_change': 'true',
                        'include_24hr_vol': 'true',
                    }
                    response = await client.get(url, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        if coin_id in data:
                            price_data = data[coin_id]
                            update = {
                                'type': 'price_update',
                                'symbol': symbol.upper(),
                                'price': price_data.get('usd', 0),
                                'change_24h': price_data.get('usd_24h_change', 0),
                                'volume_24h': price_data.get('usd_24h_vol', 0),
                            }
                            await self.send(text_data=json.dumps(update))

                    await asyncio.sleep(15)
                except asyncio.CancelledError:
                    break
                except Exception:
                    await asyncio.sleep(30)


class MultiPriceConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for multiple symbols at once."""

    async def connect(self):
        self.symbols = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP']
        self.is_connected = True
        connected_clients.add(self)

        await self.accept()
        logger.info(f"Multi-price WebSocket connected ({len(connected_clients)} total)")

        # Start polling
        self.price_task = asyncio.create_task(self._poll_all_prices())

    async def disconnect(self, close_code):
        self.is_connected = False
        connected_clients.discard(self)

        if hasattr(self, 'price_task'):
            self.price_task.cancel()
            try:
                await self.price_task
            except asyncio.CancelledError:
                pass

        logger.info(f"Multi-price WebSocket disconnected ({len(connected_clients)} total)")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action', '')

            if action == 'update_symbols':
                self.symbols = data.get('symbols', self.symbols)
                # Restart polling with new symbols
                if hasattr(self, 'price_task'):
                    self.price_task.cancel()
                self.price_task = asyncio.create_task(self._poll_all_prices())

            elif action == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))

        except json.JSONDecodeError:
            pass

    async def _poll_all_prices(self):
        """Poll all symbols in one CoinGecko call."""
        import httpx

        symbol_map = {
            'BTC': 'bitcoin', 'ETH': 'ethereum', 'SOL': 'solana',
            'BNB': 'binancecoin', 'XRP': 'ripple', 'ADA': 'cardano',
            'DOGE': 'dogecoin', 'DOT': 'polkadot', 'AVAX': 'avalanche-2',
            'LINK': 'chainlink', 'MATIC': 'matic-network', 'SHIB': 'shiba-inu',
            'LTC': 'litecoin', 'UNI': 'uniswap', 'ATOM': 'cosmos',
        }

        # Reverse map: coin_id -> symbol
        reverse_map = {v: k for k, v in symbol_map.items()}

        async with httpx.AsyncClient(timeout=10.0) as client:
            while self.is_connected:
                try:
                    coin_ids = [symbol_map.get(s.upper(), s.lower()) for s in self.symbols]
                    url = 'https://api.coingecko.com/api/v3/simple/price'
                    params = {
                        'ids': ','.join(coin_ids),
                        'vs_currencies': 'usd',
                        'include_24hr_change': 'true',
                        'include_24hr_vol': 'true',
                        'include_market_cap': 'true',
                    }

                    response = await client.get(url, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        updates = []
                        for coin_id, price_info in data.items():
                            sym = reverse_map.get(coin_id, coin_id.upper())
                            updates.append({
                                'symbol': sym,
                                'price': price_info.get('usd', 0),
                                'change_24h': price_info.get('usd_24h_change', 0),
                                'volume_24h': price_info.get('usd_24h_vol', 0),
                                'market_cap': price_info.get('usd_market_cap', 0),
                            })

                        await self.send(text_data=json.dumps({
                            'type': 'prices_batch',
                            'prices': updates,
                        }))

                    # Update every 15 seconds
                    await asyncio.sleep(15)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.warning(f"Multi-price poll error: {e}")
                    await asyncio.sleep(30)
