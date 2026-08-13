"""
Comprehensive 6-Hour BTC Feedback Loop

Scans ALL data sources every 6 hours:
1. News articles (RSS feeds) - sentiment analysis
2. Candle changes - pattern detection, volume analysis
3. Price action - support/resistance, trend changes
4. Order book - bid/ask imbalance, walls
5. Social sentiment - X/Twitter, fear/greed
6. Technical indicators - RSI, MACD, VWAP, Ichimoku
7. Macro data - BTC dominance, market cap
8. AI prediction accuracy - compare past predictions

Then:
- Evaluates past signals against actual outcomes
- Generates insights about what worked/didn't
- Adjusts factor weights based on performance
- Updates the AI learning model
- Stores everything for the feedback panel
"""
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


class BTCFeedbackLoop:
    """Comprehensive BTC feedback loop that re-learns every 6 hours."""

    @classmethod
    def run(cls) -> Dict:
        """Execute the full 6-hour feedback cycle."""
        start = time.time()
        results = {
            'cycle_type': '6hour_btc',
            'started_at': datetime.now().isoformat(),
            'sections': {},
            'insights': [],
            'weight_adjustments': {},
        }

        try:
            # 1. Scan news
            logger.info("1/8 Scanning news...")
            results['sections']['news'] = cls._scan_news()

            # 2. Analyze candle changes
            logger.info("2/8 Analyzing candle changes...")
            results['sections']['candles'] = cls._analyze_candles()

            # 3. Check price action
            logger.info("3/8 Checking price action...")
            results['sections']['price'] = cls._analyze_price()

            # 4. Read order book
            logger.info("4/8 Reading order book...")
            results['sections']['orderbook'] = cls._analyze_orderbook()

            # 5. Social sentiment
            logger.info("5/8 Scanning social sentiment...")
            results['sections']['social'] = cls._analyze_social()

            # 6. Technical indicators
            logger.info("6/8 Computing technical indicators...")
            results['sections']['technical'] = cls._analyze_technical()

            # 7. Macro data
            logger.info("7/8 Fetching macro data...")
            results['sections']['macro'] = cls._analyze_macro()

            # 8. Evaluate past signals
            logger.info("8/8 Evaluating past signals...")
            results['sections']['signal_evaluation'] = cls._evaluate_signals()

            # Generate insights from all sections
            results['insights'] = cls._generate_insights(results['sections'])

            # Adjust weights based on performance
            results['weight_adjustments'] = cls._adjust_weights(results['sections'])

            # Store results in database
            cls._store_results(results)

            # Generate learning summary
            results['learning_summary'] = cls._generate_learning_summary(results)

            elapsed = time.time() - start
            results['completed_at'] = datetime.now().isoformat()
            results['execution_time_seconds'] = round(elapsed, 1)
            results['status'] = 'success'

            logger.info(f"6-hour BTC feedback loop completed in {elapsed:.1f}s")
            return results

        except Exception as e:
            logger.error(f"6-hour BTC feedback loop failed: {e}")
            results['status'] = 'error'
            results['error'] = str(e)
            return results

    @classmethod
    def _scan_news(cls) -> Dict:
        """Scan recent news articles and analyze sentiment."""
        try:
            from apps.news.models import NewsArticle
            from django.utils import timezone

            cutoff = timezone.now() - timedelta(hours=6)
            articles = NewsArticle.objects.filter(
                published_at__gte=cutoff,
            ).order_by('-impact_score')[:30]

            if not articles.exists():
                return {'status': 'no_new_articles', 'count': 0}

            # Analyze sentiment
            bullish = 0
            bearish = 0
            neutral = 0
            high_impact = 0

            for article in articles:
                if article.sentiment == 'bullish':
                    bullish += 1
                elif article.sentiment == 'bearish':
                    bearish += 1
                else:
                    neutral += 1

                if article.impact_score >= 70:
                    high_impact += 1

            total = articles.count()
            sentiment_score = 50 + ((bullish - bearish) / max(total, 1)) * 40

            return {
                'total_articles': total,
                'bullish': bullish,
                'bearish': bearish,
                'neutral': neutral,
                'high_impact_count': high_impact,
                'sentiment_score': int(sentiment_score),
                'top_headlines': [
                    {'title': a.title[:80], 'sentiment': a.sentiment, 'impact': a.impact_score}
                    for a in articles[:5]
                ],
            }

        except Exception as e:
            logger.error(f"News scan failed: {e}")
            return {'status': 'error', 'error': str(e)}

    @classmethod
    def _analyze_candles(cls) -> Dict:
        """Analyze recent candle data for patterns and volume."""
        try:
            from apps.market.services.unified_data import fetch_market_data

            market = fetch_market_data('BTC')
            closes = market['closes']
            highs = market['highs']
            lows = market['lows']
            volumes = market['volumes']

            if len(closes) < 20:
                return {'status': 'insufficient_data', 'data_points': len(closes)}

            # Recent candles (last 12 = 12 hours if 1h candles)
            recent_closes = closes[-12:]
            recent_volumes = volumes[-12:]

            # Price change
            price_change_1h = ((closes[-1] - closes[-2]) / closes[-2]) * 100 if len(closes) >= 2 else 0
            price_change_6h = ((closes[-1] - closes[-7]) / closes[-7]) * 100 if len(closes) >= 7 else 0
            price_change_24h = ((closes[-1] - closes[-25]) / closes[-25]) * 100 if len(closes) >= 25 else 0

            # Volume analysis
            avg_volume = sum(volumes[-50:]) / min(len(volumes), 50)
            recent_avg_volume = sum(recent_volumes) / len(recent_volumes)
            volume_ratio = recent_avg_volume / max(avg_volume, 1)

            # High/Low range
            recent_high = max(highs[-12:])
            recent_low = min(lows[-12:])
            current_price = closes[-1]
            range_pct = ((recent_high - recent_low) / current_price) * 100

            # Candle patterns
            patterns = cls._detect_patterns(closes[-5:], highs[-5:], lows[-5:])

            return {
                'current_price': current_price,
                'price_change_1h': round(price_change_1h, 2),
                'price_change_6h': round(price_change_6h, 2),
                'price_change_24h': round(price_change_24h, 2),
                'recent_high': recent_high,
                'recent_low': recent_low,
                'range_percent': round(range_pct, 2),
                'volume_ratio': round(volume_ratio, 2),
                'volume_trend': 'high' if volume_ratio > 1.5 else 'low' if volume_ratio < 0.5 else 'normal',
                'patterns': patterns,
            }

        except Exception as e:
            logger.error(f"Candle analysis failed: {e}")
            return {'status': 'error', 'error': str(e)}

    @classmethod
    def _detect_patterns(cls, closes, highs, lows) -> List[str]:
        """Detect candlestick patterns."""
        patterns = []
        if len(closes) < 3:
            return patterns

        for i in range(1, len(closes)):
            body = closes[i] - closes[i-1]
            upper_shadow = highs[i] - max(closes[i], closes[i-1])
            lower_shadow = min(closes[i], closes[i-1]) - lows[i]
            body_size = abs(body)

            if body_size < (highs[i] - lows[i]) * 0.1:
                patterns.append('doji')
            elif lower_shadow > body_size * 2 and upper_shadow < body_size * 0.5:
                patterns.append('hammer' if body > 0 else 'hanging_man')
            elif upper_shadow > body_size * 2 and lower_shadow < body_size * 0.5:
                patterns.append('shooting_star' if body < 0 else 'inverted_hammer')

        return list(set(patterns))

    @classmethod
    def _analyze_price(cls) -> Dict:
        """Analyze price action for support/resistance and trends."""
        try:
            from apps.market.services.unified_data import fetch_market_data

            market = fetch_market_data('BTC')
            closes = market['closes']
            current_price = closes[-1]

            if len(closes) < 50:
                return {'status': 'insufficient_data'}

            # Moving averages
            sma_20 = sum(closes[-20:]) / 20
            sma_50 = sum(closes[-50:]) / 50
            ema_12 = cls._ema(closes, 12)
            ema_26 = cls._ema(closes, 26)

            # Trend detection
            trend = 'neutral'
            if current_price > sma_20 > sma_50:
                trend = 'uptrend'
            elif current_price < sma_20 < sma_50:
                trend = 'downtrend'
            elif current_price > sma_20:
                trend = 'weak_uptrend'
            elif current_price < sma_20:
                trend = 'weak_downtrend'

            # Support/Resistance (simple pivot points)
            recent_highs = closes[-20:]
            resistance = max(recent_highs)
            support = min(recent_highs)

            # Distance to support/resistance
            to_resistance = ((resistance - current_price) / current_price) * 100
            to_support = ((current_price - support) / current_price) * 100

            return {
                'current_price': current_price,
                'sma_20': round(sma_20, 2),
                'sma_50': round(sma_50, 2),
                'ema_12': round(ema_12, 2),
                'ema_26': round(ema_26, 2),
                'trend': trend,
                'resistance': round(resistance, 2),
                'support': round(support, 2),
                'to_resistance_pct': round(to_resistance, 2),
                'to_support_pct': round(to_support, 2),
                'price_vs_sma20': 'above' if current_price > sma_20 else 'below',
                'price_vs_sma50': 'above' if current_price > sma_50 else 'below',
            }

        except Exception as e:
            logger.error(f"Price analysis failed: {e}")
            return {'status': 'error', 'error': str(e)}

    @classmethod
    def _analyze_orderbook(cls) -> Dict:
        """Analyze order book for bid/ask imbalance."""
        try:
            # Use CoinGecko ticker for bid/ask data
            import urllib.request
            import json

            url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_vol=true&include_24hr_change=true'
            req = urllib.request.Request(url, headers={'User-Agent': 'AI-Trading-Bot/1.0'})
            response = urllib.request.urlopen(req, timeout=10)
            data = json.loads(response.read())

            btc_data = data.get('bitcoin', {})

            return {
                'source': 'coingecko',
                'volume_24h': btc_data.get('usd_24h_vol', 0),
                'change_24h': btc_data.get('usd_24h_change', 0),
                'note': 'Full order book requires exchange API keys',
            }

        except Exception as e:
            logger.error(f"Order book analysis failed: {e}")
            return {'status': 'error', 'error': str(e)}

    @classmethod
    def _analyze_social(cls) -> Dict:
        """Analyze social sentiment from X/Twitter and fear/greed."""
        try:
            from apps.journal.services.journal_writer import fetch_fear_greed_index
            import asyncio

            # Fear & Greed
            try:
                fg = fetch_fear_greed_index()
                fear_greed = fg.get('value', 50)
                fear_label = fg.get('label', 'Neutral')
            except Exception:
                fear_greed = 50
                fear_label = 'Neutral'

            # X/Twitter sentiment
            twitter_sentiment = 50
            tweet_count = 0
            try:
                from apps.social.services.twitter_scraper import TwitterScraper
                scraper = TwitterScraper()
                key_accounts = {
                    'CryptoCapo_': 'analyst',
                    'WhaleAlert': 'whale',
                    'WatcherGuru': 'news',
                    'sentdefender': 'geopolitics',
                }
                tweets = asyncio.run(scraper.fetch_all_accounts(key_accounts, limit_per_user=3))
                if tweets:
                    result = scraper.analyze_sentiment(tweets)
                    twitter_sentiment = result['score']
                    tweet_count = result['tweet_count']
            except Exception as e:
                logger.warning(f"Twitter scrape failed: {e}")

            # Combined sentiment
            combined = int((fear_greed + twitter_sentiment) / 2)

            return {
                'fear_greed_index': fear_greed,
                'fear_greed_label': fear_label,
                'twitter_sentiment': twitter_sentiment,
                'tweet_count': tweet_count,
                'combined_sentiment': combined,
                'sentiment_label': 'bullish' if combined > 60 else 'bearish' if combined < 40 else 'neutral',
            }

        except Exception as e:
            logger.error(f"Social analysis failed: {e}")
            return {'status': 'error', 'error': str(e)}

    @classmethod
    def _analyze_technical(cls) -> Dict:
        """Compute technical indicators."""
        try:
            from apps.technical_analysis.services.indicator_engine import IndicatorEngine
            from apps.market.services.unified_data import fetch_market_data

            market = fetch_market_data('BTC')
            closes = market['closes']
            highs = market['highs']
            lows = market['lows']
            volumes = market['volumes']

            if len(closes) < 30:
                return {'status': 'insufficient_data'}

            indicators = IndicatorEngine.calculate_all_indicators(
                [{'close': c, 'high': h, 'low': l, 'volume': v}
                 for c, h, l, v in zip(closes[-100:], highs[-100:], lows[-100:], volumes[-100:])]
            )

            rsi = indicators.get('rsi_14', {})
            macd = indicators.get('macd', {})
            ema9 = indicators.get('ema_9', {})
            ema21 = indicators.get('ema_21', {})
            vwap = indicators.get('vwap', {})

            return {
                'rsi': rsi.get('value', 50),
                'rsi_signal': rsi.get('signal', 'neutral'),
                'macd_trend': macd.get('trend', 'neutral'),
                'macd_histogram': macd.get('histogram', 0),
                'ema9_signal': ema9.get('signal', 'neutral'),
                'ema21_signal': ema21.get('signal', 'neutral'),
                'vwap_signal': vwap.get('signal', 'neutral'),
                'vwap_value': vwap.get('value', 0),
                'overall_score': indicators.get('overall_score', 50),
            }

        except Exception as e:
            logger.error(f"Technical analysis failed: {e}")
            return {'status': 'error', 'error': str(e)}

    @classmethod
    def _analyze_macro(cls) -> Dict:
        """Analyze macro data."""
        try:
            import urllib.request
            import json

            url = 'https://api.coingecko.com/api/v3/global'
            req = urllib.request.Request(url, headers={'User-Agent': 'AI-Trading-Bot/1.0'})
            response = urllib.request.urlopen(req, timeout=10)
            data = json.loads(response.read())

            global_data = data.get('data', {})
            btc_dominance = global_data.get('market_cap_percentage', {}).get('btc', 50)
            total_cap_change = global_data.get('market_cap_change_percentage_24h_usd', 0)

            return {
                'btc_dominance': round(btc_dominance, 2),
                'total_market_cap_change_24h': round(total_cap_change, 2),
                'market_regime': 'bullish' if total_cap_change > 2 else 'bearish' if total_cap_change < -2 else 'neutral',
                'btc_trend_from_dominance': 'bullish' if btc_dominance > 55 else 'bearish' if btc_dominance < 45 else 'neutral',
            }

        except Exception as e:
            logger.error(f"Macro analysis failed: {e}")
            return {'status': 'error', 'error': str(e)}

    @classmethod
    def _evaluate_signals(cls) -> Dict:
        """Evaluate past signals against actual outcomes."""
        try:
            from apps.signals.models import Signal
            from apps.feedback.models import SignalMemory
            from apps.market.services.unified_data import fetch_market_data
            from datetime import timedelta

            # Get signals from last 6 hours
            cutoff = datetime.now() - timedelta(hours=6)
            recent_signals = Signal.objects.filter(
                created_at__gte=cutoff,
                symbol='BTC',
            )

            if not recent_signals.exists():
                return {'status': 'no_signals', 'count': 0}

            # Get current price
            market = fetch_market_data('BTC')
            current_price = market['current_price']

            evaluated = 0
            wins = 0
            losses = 0

            for signal in recent_signals:
                # Check if already evaluated
                if SignalMemory.objects.filter(signal=signal).exists():
                    continue

                # Calculate outcome
                if signal.direction in ('buy', 'strong_buy'):
                    pnl = ((current_price - signal.entry_price) / signal.entry_price) * 100
                else:
                    pnl = ((signal.entry_price - current_price) / signal.entry_price) * 100

                was_correct = pnl > 0

                # Record outcome
                SignalMemory.objects.create(
                    signal=signal,
                    signal_direction=signal.direction,
                    signal_confidence=signal.confidence,
                    entry_price=signal.entry_price,
                    exit_price=current_price,
                    actual_return=Decimal('0'),
                    actual_return_percent=Decimal(str(round(pnl, 2))),
                    was_correct=was_correct,
                    holding_period_hours=6,
                    factors_at_creation={
                        'technical_score': float(signal.technical_score),
                        'sentiment_score': float(signal.sentiment_score),
                        'news_score': float(signal.news_score),
                        'ai_score': float(signal.ai_score),
                        'macro_score': float(signal.macro_score),
                        'composite_score': float(signal.composite_score),
                    },
                    evaluated_at=datetime.now(),
                )

                evaluated += 1
                if was_correct:
                    wins += 1
                else:
                    losses += 1

            win_rate = (wins / max(evaluated, 1)) * 100

            return {
                'signals_evaluated': evaluated,
                'wins': wins,
                'losses': losses,
                'win_rate': round(win_rate, 1),
                'current_price': current_price,
            }

        except Exception as e:
            logger.error(f"Signal evaluation failed: {e}")
            return {'status': 'error', 'error': str(e)}

    @classmethod
    def _generate_insights(cls, sections: Dict) -> List[Dict]:
        """Generate actionable insights from all data sources."""
        insights = []

        # News insight
        news = sections.get('news', {})
        if news.get('sentiment_score', 50) > 65:
            insights.append({
                'type': 'news',
                'severity': 'info',
                'message': f"News sentiment is bullish ({news['sentiment_score']}/100) with {news.get('high_impact_count', 0)} high-impact articles",
            })
        elif news.get('sentiment_score', 50) < 35:
            insights.append({
                'type': 'news',
                'severity': 'warning',
                'message': f"News sentiment is bearish ({news['sentiment_score']}/100) — potential downside risk",
            })

        # Price insight
        price = sections.get('price', {})
        if price.get('trend') in ('uptrend', 'downtrend'):
            insights.append({
                'type': 'price',
                'severity': 'info',
                'message': f"BTC in {price['trend']} — price {'above' if 'up' in price['trend'] else 'below'} SMA20 & SMA50",
            })

        # Social insight
        social = sections.get('social', {})
        if social.get('combined_sentiment', 50) > 70:
            insights.append({
                'type': 'social',
                'severity': 'info',
                'message': f"Social sentiment bullish ({social['combined_sentiment']}/100) — F&G: {social.get('fear_greed_index', 50)}",
            })
        elif social.get('combined_sentiment', 50) < 30:
            insights.append({
                'type': 'social',
                'severity': 'warning',
                'message': f"Social sentiment bearish ({social['combined_sentiment']}/100) — extreme fear in market",
            })

        # Technical insight
        tech = sections.get('technical', {})
        if tech.get('rsi', 50) > 70:
            insights.append({
                'type': 'technical',
                'severity': 'warning',
                'message': f"RSI overbought ({tech['rsi']}) — potential pullback",
            })
        elif tech.get('rsi', 50) < 30:
            insights.append({
                'type': 'technical',
                'severity': 'opportunity',
                'message': f"RSI oversold ({tech['rsi']}) — potential bounce",
            })

        # Signal evaluation insight
        evaluation = sections.get('signal_evaluation', {})
        if evaluation.get('signals_evaluated', 0) > 0:
            win_rate = evaluation.get('win_rate', 0)
            insights.append({
                'type': 'performance',
                'severity': 'info' if win_rate > 50 else 'warning',
                'message': f"Last 6h: {evaluation['signals_evaluated']} signals, {win_rate}% win rate ({evaluation['wins']}W/{evaluation['losses']}L)",
            })

        return insights

    @classmethod
    def _adjust_weights(cls, sections: Dict) -> Dict:
        """Adjust factor weights based on performance."""
        try:
            from apps.signals.services.weight_adjuster import WeightAdjuster

            result = WeightAdjuster.adjust_weights(lookback_days=1)
            return result

        except Exception as e:
            logger.error(f"Weight adjustment failed: {e}")
            return {'status': 'error', 'error': str(e)}

    @classmethod
    def _store_results(cls, results: Dict):
        """Store feedback loop results in database."""
        try:
            from apps.feedback.models import FeedbackCycle

            # Build summary from insights
            insights = results.get('insights', [])
            summary_parts = [i.get('message', '') for i in insights]
            summary = '\n'.join(summary_parts) if summary_parts else 'No insights generated'

            # Check if any weights were adjusted
            adj = results.get('weight_adjustments', {})
            weights_adjusted = adj.get('status') == 'complete' and adj.get('weights_changed', False)

            # Count signals evaluated
            eval_data = results.get('sections', {}).get('signal_evaluation', {})
            signals_evaluated = eval_data.get('signals_evaluated', 0)
            signals_correct = eval_data.get('wins', 0)

            FeedbackCycle.objects.create(
                cycle_type='6hour_btc',
                status=results['status'],
                signals_evaluated=signals_evaluated,
                signals_correct=signals_correct,
                insights_generated=len(insights),
                weights_adjusted=weights_adjusted,
                summary=summary,
                recommendations=[i.get('message', '') for i in insights if i.get('severity') in ('warning', 'opportunity')],
            )

        except Exception as e:
            logger.error(f"Failed to store results: {e}")

    @classmethod
    def _generate_learning_summary(cls, results: Dict) -> Dict:
        """Generate a learning summary for the AI."""
        sections = results.get('sections', {})

        # Build comprehensive summary
        summary = {
            'btc_status': {},
            'key_factors': [],
            'recommendation': 'HOLD',
            'confidence': 50,
        }

        # Collect all scores
        scores = {}
        for section_name, section_data in sections.items():
            if isinstance(section_data, dict):
                for key in ['sentiment_score', 'combined_sentiment', 'overall_score', 'win_rate']:
                    if key in section_data:
                        scores[f"{section_name}_{key}"] = section_data[key]

        # Determine recommendation
        bullish_factors = 0
        bearish_factors = 0

        price = sections.get('price', {})
        if price.get('trend', '').startswith('up'):
            bullish_factors += 1
        elif price.get('trend', '').startswith('down'):
            bearish_factors += 1

        tech = sections.get('technical', {})
        if tech.get('rsi', 50) < 40:
            bullish_factors += 1
        elif tech.get('rsi', 50) > 60:
            bearish_factors += 1

        social = sections.get('social', {})
        if social.get('combined_sentiment', 50) > 60:
            bullish_factors += 1
        elif social.get('combined_sentiment', 50) < 40:
            bearish_factors += 1

        macro = sections.get('macro', {})
        if macro.get('market_regime') == 'bullish':
            bullish_factors += 1
        elif macro.get('market_regime') == 'bearish':
            bearish_factors += 1

        total = bullish_factors + bearish_factors
        if total > 0:
            if bullish_factors > bearish_factors:
                summary['recommendation'] = 'BUY'
                summary['confidence'] = min(80, 50 + (bullish_factors - bearish_factors) * 10)
            elif bearish_factors > bullish_factors:
                summary['recommendation'] = 'SELL'
                summary['confidence'] = min(80, 50 + (bearish_factors - bullish_factors) * 10)

        summary['bullish_factors'] = bullish_factors
        summary['bearish_factors'] = bearish_factors

        return summary

    @staticmethod
    def _ema(data, period):
        """Calculate EMA."""
        if len(data) < period:
            return data[-1] if data else 0
        multiplier = 2 / (period + 1)
        ema = sum(data[:period]) / period
        for price in data[period:]:
            ema = (price - ema) * multiplier + ema
        return ema
