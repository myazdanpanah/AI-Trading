"""WebSocket consumers for real-time market data streaming."""
import json
import asyncio
from datetime import datetime
from decimal import Decimal
from channels.generic.websocket import AsyncWebSocketConsumer
from channels.db import database_sync_to_async


class PriceConsumer(AsyncWebSocketConsumer):
    """WebSocket consumer for real-time price streaming."""
    
    async def connect(self):
        self.symbol = self.scope['url_route']['kwargs']['symbol'].replace('-', '/')
        self.room_group_name = f'prices_{self.symbol}'
        
        # Join price group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Start sending price updates
        self.price_task = asyncio.create_task(self.send_price_updates())
    
    async def disconnect(self, close_code):
        # Cancel price updates
        if hasattr(self, 'price_task'):
            self.price_task.cancel()
        
        # Leave price group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming messages from client."""
        try:
            data = json.loads(text_data)
            if data.get('type') == 'subscribe':
                self.symbol = data.get('symbol', self.symbol).replace('-', '/')
                self.room_group_name = f'prices_{self.symbol}'
                
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
        except json.JSONDecodeError:
            pass
    
    async def send_price_updates(self):
        """Send simulated price updates every second."""
        base_price = self._get_base_price()
        
        while True:
            try:
                # Generate realistic price movement
                change = (asyncio.get_event_loop().time() % 10 - 5) * 0.001
                current_price = base_price * (1 + change)
                
                # Generate OHLCV data
                open_price = current_price * (1 - 0.001)
                high_price = current_price * (1 + 0.002)
                low_price = current_price * (1 - 0.002)
                volume = 1000000 + (hash(str(datetime.now())) % 500000)
                
                price_data = {
                    'type': 'price_update',
                    'symbol': self.symbol,
                    'price': float(current_price),
                    'open': float(open_price),
                    'high': float(high_price),
                    'low': float(low_price),
                    'close': float(current_price),
                    'volume': volume,
                    'change_24h': round(change * 100, 2),
                    'timestamp': datetime.now().isoformat(),
                }
                
                await self.send(text_data=json.dumps(price_data))
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Price update error: {e}")
                await asyncio.sleep(1)
    
    def _get_base_price(self):
        """Get base price for the symbol."""
        prices = {
            'BTC/USDT': 67500.0,
            'ETH/USDT': 3450.0,
            'SOL/USDT': 180.0,
            'BNB/USDT': 620.0,
            'XRP/USDT': 0.62,
            'ADA/USDT': 0.45,
            'DOGE/USDT': 0.12,
            'DOT/USDT': 7.5,
            'AVAX/USDT': 38.0,
            'LINK/USDT': 15.0,
        }
        return prices.get(self.symbol, 100.0)
    
    async def price_update(self, event):
        """Send price update to WebSocket."""
        await self.send(text_data=json.dumps(event['data']))


class OrderBookConsumer(AsyncWebSocketConsumer):
    """WebSocket consumer for real-time order book streaming."""
    
    async def connect(self):
        self.symbol = self.scope['url_route']['kwargs']['symbol'].replace('-', '/')
        self.room_group_name = f'orderbook_{self.symbol}'
        
        # Join order book group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Start sending order book updates
        self.orderbook_task = asyncio.create_task(self.send_orderbook_updates())
    
    async def disconnect(self, close_code):
        # Cancel updates
        if hasattr(self, 'orderbook_task'):
            self.orderbook_task.cancel()
        
        # Leave group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def send_orderbook_updates(self):
        """Send simulated order book updates every 1.5 seconds."""
        base_price = self._get_base_price()
        
        while True:
            try:
                # Generate order book data
                bids = []
                asks = []
                
                for i in range(10):
                    bid_price = base_price - (i + 1) * (3 + (hash(str(i)) % 8))
                    ask_price = base_price + (i + 1) * (3 + (hash(str(i)) % 8))
                    
                    bid_amount = 0.01 + (hash(str(i) + 'bid') % 500) / 10000
                    ask_amount = 0.01 + (hash(str(i) + 'ask') % 500) / 10000
                    
                    bids.append({
                        'price': round(bid_price, 2),
                        'amount': round(bid_amount, 4),
                        'total': round(sum(b['amount'] for b in bids) + bid_amount, 4),
                    })
                    
                    asks.append({
                        'price': round(ask_price, 2),
                        'amount': round(ask_amount, 4),
                        'total': round(sum(a['amount'] for a in asks) + ask_amount, 4),
                    })
                
                spread = asks[0]['price'] - bids[0]['price']
                
                orderbook_data = {
                    'type': 'orderbook_update',
                    'symbol': self.symbol,
                    'bids': bids,
                    'asks': asks,
                    'spread': round(spread, 2),
                    'last_price': base_price,
                    'timestamp': datetime.now().isoformat(),
                }
                
                await self.send(text_data=json.dumps(orderbook_data))
                await asyncio.sleep(1.5)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Order book update error: {e}")
                await asyncio.sleep(1.5)
    
    def _get_base_price(self):
        """Get base price for the symbol."""
        prices = {
            'BTC/USDT': 67500.0,
            'ETH/USDT': 3450.0,
            'SOL/USDT': 180.0,
            'BNB/USDT': 620.0,
            'XRP/USDT': 0.62,
            'ADA/USDT': 0.45,
            'DOGE/USDT': 0.12,
            'DOT/USDT': 7.5,
            'AVAX/USDT': 38.0,
            'LINK/USDT': 15.0,
        }
        return prices.get(self.symbol, 100.0)
    
    async def orderbook_update(self, event):
        """Send order book update to WebSocket."""
        await self.send(text_data=json.dumps(event['data']))
