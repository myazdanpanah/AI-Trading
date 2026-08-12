"""Management command to collect candle data for AI training."""
from django.core.management.base import BaseCommand
from apps.feedback.services.candle_collector import candle_collector


class Command(BaseCommand):
    help = 'Collect candle data from CoinGecko for AI training'
    
    def add_arguments(self, parser):
        parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Symbol to collect')
        parser.add_argument('--timeframe', type=str, default='1h', help='Timeframe')
        parser.add_argument('--limit', type=int, default=100, help='Number of candles')
        parser.add_argument('--all', action='store_true', help='Collect for all watchlist symbols')
    
    def handle(self, *args, **options):
        if options['all']:
            symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT']
        else:
            symbols = [options['symbol']]
        
        timeframe = options['timeframe']
        limit = options['limit']
        
        self.stdout.write(f"Collecting candles for {symbols} ({timeframe}, limit={limit})")
        
        for symbol in symbols:
            try:
                result = candle_collector.collect_candles(symbol, timeframe, limit)
                if 'error' in result:
                    self.stdout.write(self.style.ERROR(f"  {symbol}: {result['error']}"))
                else:
                    self.stdout.write(self.style.SUCCESS(
                        f"  {symbol}: stored {result['stored']}/{result['total']} candles"
                    ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  {symbol}: {e}"))
        
        # Show stats
        from apps.feedback.models import CandleData, TrainingSample
        candle_count = CandleData.objects.count()
        sample_count = TrainingSample.objects.count()
        self.stdout.write(f"\nTotal candles in database: {candle_count}")
        self.stdout.write(f"Total training samples: {sample_count}")
