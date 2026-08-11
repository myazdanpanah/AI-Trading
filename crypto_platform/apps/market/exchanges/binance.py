"""Binance exchange connector."""
import ccxt.async_support as ccxt
from .ccxt_base import CCXTExchange


class BinanceExchange(CCXTExchange):
    """Binance exchange connector."""
    
    exchange_class = ccxt.binance
    default_config = {
        'options': {
            'defaultType': 'spot',
        }
    }
    
    def __init__(self, api_key: str = '', api_secret: str = '', testnet: bool = False):
        super().__init__(api_key, api_secret, testnet)
        self.name = 'binance'
