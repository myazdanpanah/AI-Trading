"""
Standalone Scheduler — Full Backup for Celery
Runs ALL scheduled tasks without Celery/Redis.

Covers all 10 Celery beat tasks:
1. News crawl every 30 minutes
2. News analysis every hour
3. Signal generation every hour
4. Signal evaluation every hour
5. Daily feedback cycle at 1 AM
6. Weight adjustment daily at 2 AM
7. Weekly cycle Sunday at 2 AM
8. Candle collection every 4 hours
9. BTC 6-hour comprehensive feedback loop
10. Cleanup old memories monthly

Usage:
  python scripts/scheduler.py
"""
import os
import sys
import time
import signal
import logging
from datetime import datetime, timedelta
import calendar

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

running = True

def shutdown(signum, frame):
    global running
    logger.info('Shutting down scheduler...')
    running = False

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)


# ============================================================
# TASK FUNCTIONS
# ============================================================

def run_news_crawl():
    """Crawl news from RSS feeds (every 30 min)."""
    try:
        from apps.news.tasks import crawl_news_sources
        logger.info('Crawling news feeds...')
        result = crawl_news_sources()
        logger.info(f'News crawl complete: {result}')
    except Exception as e:
        logger.error(f'News crawl failed: {e}')


def run_news_analyze():
    """Analyze unanalyzed news articles (every hour)."""
    try:
        from apps.news.tasks import analyze_news_batch
        logger.info('Analyzing news batch...')
        result = analyze_news_batch()
        logger.info(f'News analysis complete: {result}')
    except Exception as e:
        logger.error(f'News analysis failed: {e}')


def run_signal_generation():
    """Generate signals for all symbols (every hour)."""
    try:
        from apps.feedback.tasks import generate_signals_hourly
        logger.info('Generating hourly signals...')
        result = generate_signals_hourly()
        logger.info(f'Signal generation complete: {result}')
    except Exception as e:
        logger.error(f'Signal generation failed: {e}')


def run_signal_evaluation():
    """Evaluate pending signals (every hour)."""
    try:
        from apps.feedback.tasks import evaluate_signals_hourly
        logger.info('Evaluating signals...')
        result = evaluate_signals_hourly()
        logger.info(f'Signal evaluation complete: {result}')
    except Exception as e:
        logger.error(f'Signal evaluation failed: {e}')


def run_daily_feedback():
    """Run daily feedback cycle (1 AM)."""
    try:
        from apps.feedback.tasks import run_daily_feedback_cycle
        logger.info('Running daily feedback cycle...')
        result = run_daily_feedback_cycle()
        logger.info(f'Daily feedback complete: {result}')
    except Exception as e:
        logger.error(f'Daily feedback failed: {e}')


def run_weight_adjustment():
    """Adjust signal weights (2 AM)."""
    try:
        from apps.feedback.tasks import adjust_weights_daily
        logger.info('Adjusting weights...')
        result = adjust_weights_daily()
        logger.info(f'Weight adjustment complete: {result}')
    except Exception as e:
        logger.error(f'Weight adjustment failed: {e}')


def run_weekly_feedback():
    """Run weekly comprehensive feedback cycle (Sunday 2 AM)."""
    try:
        from apps.feedback.tasks import run_weekly_feedback_cycle
        logger.info('Running weekly feedback cycle...')
        result = run_weekly_feedback_cycle()
        logger.info(f'Weekly feedback complete: {result}')
    except Exception as e:
        logger.error(f'Weekly feedback failed: {e}')


def run_candle_collection():
    """Collect candle data for AI training (every 4 hours)."""
    try:
        from apps.feedback.tasks import collect_candles_task
        logger.info('Collecting candle data...')
        result = collect_candles_task()
        logger.info(f'Candle collection complete: {result}')
    except Exception as e:
        logger.error(f'Candle collection failed: {e}')


def run_btc_6hour():
    """Run comprehensive BTC feedback loop (every 6 hours)."""
    try:
        from apps.feedback.services.btc_feedback_loop import BTCFeedbackLoop
        logger.info('Starting BTC 6-hour feedback loop...')
        result = BTCFeedbackLoop.run()
        logger.info(f'BTC feedback loop complete: {result.get("status")} '
                    f'({result.get("execution_time_seconds", 0)}s, '
                    f'{len(result.get("insights", []))} insights)')
    except Exception as e:
        logger.error(f'BTC feedback loop failed: {e}')


def run_cleanup():
    """Clean up old memories (monthly, 1st at 3 AM)."""
    try:
        from apps.feedback.tasks import cleanup_old_memories
        logger.info('Cleaning up old memories...')
        result = cleanup_old_memories(days_to_keep=90)
        logger.info(f'Cleanup complete: {result}')
    except Exception as e:
        logger.error(f'Cleanup failed: {e}')


# ============================================================
# SCHEDULE DEFINITION
# ============================================================
# Each task: (interval_seconds or None, hour, minute, day_of_week, day_of_month, func, name)
# If interval_seconds is set, it runs on that interval.
# If hour/minute are set, it runs at that specific time daily/weekly/monthly.

TASKS = [
    # Every 30 minutes
    {'name': 'news-crawl', 'interval': 1800, 'func': run_news_crawl, 'desc': 'News RSS crawl'},
    # Every hour
    {'name': 'news-analyze', 'interval': 3600, 'func': run_news_analyze, 'desc': 'News analysis'},
    {'name': 'signals-generate', 'interval': 3600, 'func': run_signal_generation, 'desc': 'Signal generation'},
    {'name': 'signals-evaluate', 'interval': 3600, 'func': run_signal_evaluation, 'desc': 'Signal evaluation'},
    # Every 4 hours
    {'name': 'candles-collect', 'interval': 14400, 'func': run_candle_collection, 'desc': 'Candle collection'},
    # Every 6 hours
    {'name': 'btc-6hour', 'interval': 21600, 'func': run_btc_6hour, 'desc': 'BTC 6h feedback loop'},
    # Daily at 1 AM
    {'name': 'daily-feedback', 'interval': None, 'hour': 1, 'minute': 0, 'func': run_daily_feedback, 'desc': 'Daily feedback cycle'},
    # Daily at 2 AM
    {'name': 'weight-adjust', 'interval': None, 'hour': 2, 'minute': 0, 'func': run_weight_adjustment, 'desc': 'Weight adjustment'},
    # Weekly Sunday 2 AM
    {'name': 'weekly-feedback', 'interval': None, 'hour': 2, 'minute': 0, 'day_of_week': 6, 'func': run_weekly_feedback, 'desc': 'Weekly feedback cycle'},
    # Monthly 1st at 3 AM
    {'name': 'cleanup', 'interval': None, 'hour': 3, 'minute': 0, 'day_of_month': 1, 'func': run_cleanup, 'desc': 'Monthly cleanup'},
]


def get_next_daily_time(hour, minute):
    """Get the next datetime for a daily task."""
    now = datetime.now()
    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if next_run <= now:
        next_run += timedelta(days=1)
    return next_run


def get_next_weekly_time(hour, minute, day_of_week):
    """Get the next datetime for a weekly task."""
    now = datetime.now()
    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    days_ahead = day_of_week - now.weekday()
    if days_ahead < 0 or (days_ahead == 0 and next_run <= now):
        days_ahead += 7
    return next_run + timedelta(days=days_ahead)


def get_next_monthly_time(hour, minute, day_of_month):
    """Get the next datetime for a monthly task."""
    now = datetime.now()
    year, month = now.year, now.month
    # Try this month first
    try:
        next_run = now.replace(day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)
    except ValueError:
        # Day doesn't exist this month, try next month
        if month == 12:
            year, month = year + 1, 1
        else:
            month += 1
        last_day = calendar.monthrange(year, month)[1]
        day = min(day_of_month, last_day)
        next_run = datetime(year, month, day, hour, minute)
    if next_run <= now:
        # Move to next month
        if month == 12:
            year, month = year + 1, 1
        else:
            month += 1
        last_day = calendar.monthrange(year, month)[1]
        day = min(day_of_month, last_day)
        next_run = datetime(year, month, day, hour, minute)
    return next_run


def main():
    logger.info('=== STANDALONE SCHEDULER STARTED ===')
    logger.info('Covering all 10 Celery tasks (backup mode)')
    logger.info('')

    for task in TASKS:
        if task.get('interval'):
            h = task['interval'] // 3600
            m = (task['interval'] % 3600) // 60
            logger.info(f"  [{task['name']}] every {h}h {m}m - {task['desc']}")
        else:
            dow = task.get('day_of_week')
            dom = task.get('day_of_month')
            time_str = f"{task['hour']:02d}:{task['minute']:02d}"
            if dow is not None:
                days = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
                logger.info(f"  [{task['name']}] {days[dow]} {time_str} - {task['desc']}")
            elif dom is not None:
                logger.info(f"  [{task['name']}] {dom}th of month {time_str} - {task['desc']}")
            else:
                logger.info(f"  [{task['name']}] daily {time_str} - {task['desc']}")

    logger.info('')

    # Initialize next run times
    next_runs = {}
    for task in TASKS:
        name = task['name']
        if task.get('interval'):
            next_runs[name] = datetime.now() + timedelta(seconds=task['interval'])
        elif task.get('day_of_week') is not None:
            next_runs[name] = get_next_weekly_time(task['hour'], task['minute'], task['day_of_week'])
        elif task.get('day_of_month') is not None:
            next_runs[name] = get_next_monthly_time(task['hour'], task['minute'], task['day_of_month'])
        else:
            next_runs[name] = get_next_daily_time(task['hour'], task['minute'])

    # Main loop
    while running:
        now = datetime.now()

        for task in TASKS:
            name = task['name']
            if now >= next_runs[name]:
                logger.info(f'--- Running: {task["desc"]} ---')
                try:
                    task['func']()
                except Exception as e:
                    logger.error(f'Task {name} crashed: {e}')

                # Schedule next run
                if task.get('interval'):
                    next_runs[name] = datetime.now() + timedelta(seconds=task['interval'])
                elif task.get('day_of_week') is not None:
                    next_runs[name] = get_next_weekly_time(task['hour'], task['minute'], task['day_of_week'])
                elif task.get('day_of_month') is not None:
                    next_runs[name] = get_next_monthly_time(task['hour'], task['minute'], task['day_of_month'])
                else:
                    next_runs[name] = get_next_daily_time(task['hour'], task['minute'])

                logger.info(f'  Next run: {next_runs[name].strftime("%Y-%m-%d %H:%M:%S")}')

        # Sleep 30 seconds between checks
        for _ in range(30):
            if not running:
                break
            time.sleep(1)

    logger.info('=== SCHEDULER STOPPED ===')


if __name__ == '__main__':
    main()
