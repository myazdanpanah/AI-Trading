"""OKX exchange connector."""
import ccxt.async_support as ccxt
from .ccxt_base import CCXTExchange


class OKXExchange(CCXTExchange):
    """OKX exchange connector."""
    
    exchange_class = ccxt.okx
    default_config = {
        'options': {
            'defaultType': 'swap',
        }
    }
    
    def __init__(self, api_key: str = '', api_secret: str = '', password: str = '', testnet: bool = False):
        super().__init__(api_key, api_secret, testnet, password=password)
        self.name = 'okx'
