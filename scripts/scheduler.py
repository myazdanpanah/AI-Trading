"""
Standalone Scheduler — Backup for Celery
Runs scheduled tasks without Celery/Redis.

Usage:
  python scripts/scheduler.py

Runs:
  - Every 6 hours: BTC feedback loop
  - Every hour: signal generation
  - Every 30 minutes: news crawl
"""
import os
import sys
import time
import signal
import logging
from datetime import datetime, timedelta

# Setup Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'crypto_platform.settings.local'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
django.setup()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scheduler.log'),
    ]
)
logger = logging.getLogger('scheduler')

# Task schedule (interval_seconds, function, description)
TASKS = [
    (21600, 'feedback', '6-hour BTC feedback loop'),       # 6 hours
    (3600, 'signals', 'hourly signal generation'),          # 1 hour
    (1800, 'news', 'news crawl'),                           # 30 min
]

running = True

def shutdown(signum, frame):
    global running
    logger.info('Shutting down scheduler...')
    running = False

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)


def run_feedback():
    """Run the 6-hour BTC feedback loop."""
    try:
        from apps.feedback.services.btc_feedback_loop import BTCFeedbackLoop
        logger.info('Starting BTC feedback loop...')
        results = BTCFeedbackLoop.run()
        logger.info(f'Feedback loop finished in {results.get("execution_time_seconds", 0)}s')
        return results
    except Exception as e:
        logger.error(f'Feedback loop failed: {e}')
        return None


def run_signals():
    """Generate signals for top coins."""
    try:
        from apps.signals.services.cached_signal_generator import CachedSignalGenerator
        from apps.market.services.unified_data import get_all_market_data
        
        logger.info('Generating signals...')
        data = get_all_market_data(['BTC', 'ETH', 'SOL', 'BNB', 'XRP'])
        
        from apps.signals.services.signal_generator import SignalGenerator
        gen = SignalGenerator()
        count = 0
        for symbol, market_data in data.items():
            try:
                sig = gen.generate_signal(
                    symbol=symbol,
                    timeframe='1h',
                    technical_data=market_data.get('technical', {}),
                    sentiment_data=market_data.get('sentiment', {}),
                    current_price=market_data.get('current_price', 0),
                )
                if sig:
                    count += 1
            except Exception as e:
                logger.warning(f'  Signal gen failed for {symbol}: {e}')
        
        logger.info(f'Generated {count} signals')
    except Exception as e:
        logger.error(f'Signal generation failed: {e}')


def run_news():
    """Crawl news from RSS feeds."""
    try:
        from apps.news.crawlers.rss_crawler import RSSCrawler
        logger.info('Crawling news feeds...')
        crawler = RSSCrawler()
        count = crawler.crawl_all()
        logger.info(f'Crawled {count} articles')
    except Exception as e:
        logger.error(f'News crawl failed: {e}')


TASK_FUNCS = {
    'feedback': run_feedback,
    'signals': run_signals,
    'news': run_news,
}


def main():
    logger.info('Scheduler started')
    logger.info('Tasks:')
    for interval, name, desc in TASKS:
        logger.info(f'  {desc}: every {interval // 3600}h {(interval % 3600) // 60}m')
    
    # Track last run times
    last_runs = {name: datetime.now() for _, name, _ in TASKS}
    
    while running:
        now = datetime.now()
        
        for interval, name, desc in TASKS:
            elapsed = (now - last_runs[name]).total_seconds()
            if elapsed >= interval:
                logger.info(f'Running: {desc}')
                func = TASK_FUNCS.get(name)
                if func:
                    func()
                last_runs[name] = now
        
        # Sleep 30 seconds between checks
        for _ in range(30):
            if not running:
                break
            time.sleep(1)
    
    logger.info('Scheduler stopped')


if __name__ == '__main__':
    main()
