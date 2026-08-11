"""Bybit exchange connector."""
import ccxt.async_support as ccxt
from .ccxt_base import CCXTExchange


class BybitExchange(CCXTExchange):
    """Bybit exchange connector."""
    
    exchange_class = ccxt.bybit
    default_config = {
        'options': {
            'defaultType': 'swap',
        }
    }
    
    def __init__(self, api_key: str = '', api_secret: str = '', testnet: bool = False):
        super().__init__(api_key, api_secret, testnet)
        self.name = 'bybit'
