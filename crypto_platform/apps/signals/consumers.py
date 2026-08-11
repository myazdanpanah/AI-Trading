"""WebSocket consumer for real-time signal streaming."""
import json
import asyncio
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer


class SignalConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time trading signal updates."""
    
    async def connect(self):
        self.room_group_name = 'signals'
        
        # Join signals group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send welcome message
        await self.send(text_data=json.dumps({
            'type': 'connected',
            'message': 'Connected to signal stream',
            'timestamp': datetime.now().isoformat(),
        }))
    
    async def disconnect(self, close_code):
        # Leave signals group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming messages from client."""
        try:
            data = json.loads(text_data)
            
            if data.get('type') == 'subscribe':
                # Client can request specific symbols
                symbols = data.get('symbols', ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'])
                await self.send(text_data=json.dumps({
                    'type': 'subscribed',
                    'symbols': symbols,
                    'timestamp': datetime.now().isoformat(),
                }))
            
            elif data.get('type') == 'request_signal':
                # Client requests a signal generation
                symbol = data.get('symbol', 'BTC/USDT')
                timeframe = data.get('timeframe', '1h')
                
                # Generate mock signal for now
                signal = self._generate_mock_signal(symbol, timeframe)
                
                await self.send(text_data=json.dumps({
                    'type': 'signal_update',
                    'signal': signal,
                    'timestamp': datetime.now().isoformat(),
                }))
                
        except json.JSONDecodeError:
            pass
    
    def _generate_mock_signal(self, symbol, timeframe):
        """Generate a mock trading signal."""
        import random
        
        direction = random.choice(['buy', 'sell', 'strong_buy', 'strong_sell', 'hold'])
        confidence = random.randint(40, 95)
        risk_score = random.randint(20, 70)
        
        prices = {
            'BTC/USDT': 67500.0,
            'ETH/USDT': 3450.0,
            'SOL/USDT': 180.0,
        }
        base_price = prices.get(symbol, 100.0)
        
        entry_price = base_price * (1 + random.uniform(-0.01, 0.01))
        
        if direction in ['buy', 'strong_buy']:
            stop_loss = entry_price * 0.97
            take_profit = [entry_price * 1.03, entry_price * 1.05, entry_price * 1.08]
        elif direction in ['sell', 'strong_sell']:
            stop_loss = entry_price * 1.03
            take_profit = [entry_price * 0.97, entry_price * 0.95, entry_price * 0.92]
        else:
            stop_loss = None
            take_profit = []
        
        return {
            'id': str(int(datetime.now().timestamp() * 1000)),
            'symbol': symbol,
            'direction': direction,
            'confidence': confidence,
            'risk_score': risk_score,
            'entry_price': round(entry_price, 2),
            'stop_loss': round(stop_loss, 2) if stop_loss else None,
            'take_profit': [round(tp, 2) for tp in take_profit],
            'timeframe': timeframe,
            'composite_score': round(confidence * 0.8 + (100 - risk_score) * 0.2, 2),
            'factor_scores': {
                'technical': random.randint(40, 90),
                'sentiment': random.randint(30, 85),
                'news': random.randint(35, 80),
                'ai': random.randint(45, 95),
                'macro': random.randint(30, 75),
            },
            'reasons': [
                {
                    'type': 'technical',
                    'description': 'Strong technical indicators',
                    'confidence': random.randint(60, 90),
                }
            ],
            'created_at': datetime.now().isoformat(),
        }
    
    async def signal_update(self, event):
        """Send signal update to WebSocket."""
        await self.send(text_data=json.dumps(event['data']))
    
    async def new_signal(self, event):
        """Handle new signal from channel layer."""
        await self.send(text_data=json.dumps({
            'type': 'new_signal',
            'signal': event['signal'],
            'timestamp': datetime.now().isoformat(),
        }))
