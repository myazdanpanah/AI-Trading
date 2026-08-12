"""AI Journal Writer - Generates journal entries from market data and analysis."""
import json
import time
import urllib.request
from datetime import datetime, timezone
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Default news sources (used if no user-configured sources)
DEFAULT_NEWS_FEEDS = {
    'coindesk': {'url': 'https://www.coindesk.com/arc/outboundfeeds/rss/', 'name': 'CoinDesk', 'icon': '📰', 'category': 'crypto_news'},
    'cointelegraph': {'url': 'https://cointelegraph.com/rss', 'name': 'CoinTelegraph', 'icon': '📡', 'category': 'crypto_news'},
    'decrypt': {'url': 'https://decrypt.co/feed', 'name': 'Decrypt', 'icon': '🔐', 'category': 'crypto_news'},
    'theblock': {'url': 'https://www.theblock.co/rss.xml', 'name': 'The Block', 'icon': '🧱', 'category': 'crypto_news'},
    'bitcoin_magazine': {'url': 'https://bitcoinmagazine.com/feed', 'name': 'Bitcoin Magazine', 'icon': '₿', 'category': 'crypto_news'},
    'reuters_crypto': {'url': 'https://www.reuters.com/arc/outboundfeeds/rss/category/crypto/', 'name': 'Reuters Crypto', 'icon': '🌐', 'category': 'macro'},
    'coindesk_markets': {'url': 'https://www.coindesk.com/arc/outboundfeeds/rss/category/markets/', 'name': 'CoinDesk Markets', 'icon': '📊', 'category': 'market_data'},
}


def get_user_news_sources(user=None) -> List[Dict]:
    """Get configured news sources for user, or defaults."""
    try:
        from apps.journal.models import NewsSource
        if user:
            sources = NewsSource.objects.filter(user=user, is_active=True)
        else:
            sources = NewsSource.objects.filter(is_active=True)

        if sources.exists():
            return [
                {
                    'key': s.name.lower().replace(' ', '_'),
                    'url': s.url,
                    'name': s.name,
                    'icon': s.icon,
                    'category': s.category,
                    'source_type': s.source_type,
                    'reliability': s.reliability_score,
                }
                for s in sources
            ]
    except Exception:
        pass

    # Return defaults
    return [
        {'key': k, **v, 'source_type': 'rss', 'reliability': 70}
        for k, v in DEFAULT_NEWS_FEEDS.items()
    ]


def fetch_fear_greed_index() -> Dict:
    """Fetch Fear & Greed Index from Alternative.me."""
    try:
        url = 'https://api.alternative.me/fng/?limit=1'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        r = urllib.request.urlopen(req, timeout=10)
        data = json.loads(r.read())
        entry = data['data'][0]
        return {
            'value': int(entry['value']),
            'label': entry['value_classification'],
            'source': 'Alternative.me Fear & Greed Index',
            'timestamp': entry['timestamp'],
        }
    except Exception as e:
        logger.warning(f"Failed to fetch Fear & Greed: {e}")
        return {'value': 50, 'label': 'Neutral', 'source': 'Alternative.me', 'timestamp': str(int(time.time()))}


def fetch_news_headlines(user=None, limit: int = 15) -> List[Dict]:
    """Fetch latest crypto news headlines from configured sources."""
    try:
        import feedparser
    except ImportError:
        logger.warning("feedparser not installed")
        return []

    sources = get_user_news_sources(user)
    headlines = []

    for source in sources:
        if source.get('source_type') != 'rss':
            continue

        try:
            feed = feedparser.parse(source['url'])
            for entry in feed.entries[:3]:
                headlines.append({
                    'title': entry.get('title', ''),
                    'source': source['name'],
                    'source_icon': source.get('icon', '📰'),
                    'source_category': source.get('category', 'crypto_news'),
                    'source_reliability': source.get('reliability', 50),
                    'url': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'summary': entry.get('summary', '')[:200],
                })
        except Exception as e:
            logger.warning(f"Failed to fetch from {source['name']}: {e}")
            continue

        if len(headlines) >= limit:
            break

    return headlines[:limit]


def generate_market_summary(analysis_data: Dict, news: List[Dict], fear_greed: Dict, sources_used: List[str]) -> str:
    """Generate a comprehensive market summary prompt for the LLM."""
    price = analysis_data.get('current_price', 0)
    regime = analysis_data.get('regime', {}).get('composite', {})
    technical = analysis_data.get('technical', {})
    verdict = analysis_data.get('verdict', {})

    # Group news by source
    news_by_source = {}
    for h in news:
        src = h['source']
        if src not in news_by_source:
            news_by_source[src] = []
        news_by_source[src].append(h['title'])

    news_text = ""
    for source_name, titles in news_by_source.items():
        news_text += f"\n--- {source_name} ---\n"
        for title in titles[:3]:
            news_text += f"- {title}\n"

    sources_list = ", ".join(sources_used) if sources_used else "default sources"

    prompt = f"""You are an expert crypto market analyst writing a journal entry.

IMPORTANT: When referencing news or information, ALWAYS cite the source name.
For example: "According to CoinDesk..." or "As reported by The Block..."

Data Sources Used: {sources_list}

Current Market Data:
- BTC Price: ${price:,.2f}
- Regime Score: {regime.get('score', 'N/A')}/100 ({regime.get('zone', 'UNKNOWN')})
- Technical Score: {technical.get('overall_score', 'N/A')}/100
- RSI: {technical.get('momentum', {}).get('rsi', 'N/A')}
- Trend: {technical.get('trend', {}).get('signal', 'N/A')}
- Volatility: {technical.get('volatility', {}).get('signal', 'N/A')}
- VWAP: {technical.get('vwap', {}).get('value', 'N/A')}
- Ichimoku: {technical.get('ichimoku', {}).get('signal', 'N/A')}
- Final Verdict: {verdict.get('signal', 'N/A')} (score: {verdict.get('combined_score', 'N/A')})
- Fear & Greed: {fear_greed.get('value', 50)}/100 ({fear_greed.get('label', 'Neutral')})
  Source: {fear_greed.get('source', 'Alternative.me')}

Recent News (with sources):
{news_text}

Write a professional journal entry with these sections:

1. MARKET OVERVIEW: Current state of BTC and crypto market
2. TECHNICAL ANALYSIS: Key indicator readings and what they mean
3. NEWS & SOURCES ANALYSIS:
   - Summarize key news from each source
   - ALWAYS cite the source: "According to [Source Name]..."
   - Note which sources agree or disagree
4. SENTIMENT ANALYSIS: What the Fear & Greed index indicates
   - Reference: "Based on {fear_greed.get('source', 'Alternative.me')} data..."
5. KEY RISKS: What could go wrong
6. OPPORTUNITIES: What looks promising
7. OUTLOOK: Your 24-48 hour market outlook
8. SOURCES REFERENCED: List all sources used in this analysis

Write in a professional, analytical tone. Be specific with numbers and levels.
Keep it concise but thorough (600-900 words).
CRITICAL: Always cite sources when referencing news or data."""

    return prompt


def call_ollama(prompt: str, model: str = 'gemma4:latest') -> Optional[str]:
    """Call Ollama API for text generation."""
    try:
        data = json.dumps({
            'model': model,
            'messages': [{'role': 'user', 'content': prompt}],
            'stream': False,
            'options': {'temperature': 0.7, 'num_predict': 2500},
        }).encode('utf-8')

        req = urllib.request.Request(
            'http://localhost:11434/api/chat',
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        r = urllib.request.urlopen(req, timeout=120)
        response = json.loads(r.read())
        return response.get('message', {}).get('content', '')
    except Exception as e:
        logger.error(f"Ollama call failed: {e}")
        return None


def generate_journal_entry(analysis_data: Dict, entry_type: str = 'market_analysis', user=None) -> Dict:
    """
    Generate a complete journal entry using AI.

    Args:
        analysis_data: Full analysis from /api/skills/full-analysis/
        entry_type: Type of journal entry
        user: User object for personalized sources

    Returns:
        Dict with journal entry data ready for database storage
    """
    start = time.time()

    # Fetch supporting data
    fear_greed = fetch_fear_greed_index()
    news = fetch_news_headlines(user=user, limit=15)

    # Track which sources were used
    sources_used = list(set([n['source'] for n in news]))
    sources_used.append('CoinGecko (price data)')
    sources_used.append('Alternative.me (Fear & Greed)')

    # Generate AI content
    prompt = generate_market_summary(analysis_data, news, fear_greed, sources_used)
    ai_content = call_ollama(prompt)

    if not ai_content:
        ai_content = _generate_fallback_content(analysis_data, fear_greed, news, sources_used)

    # Extract key findings from AI content
    key_findings = _extract_findings(ai_content, 'finding')
    risks = _extract_findings(ai_content, 'risk')
    opportunities = _extract_findings(ai_content, 'opportunity')

    # Determine sentiment
    verdict = analysis_data.get('verdict', {}).get('signal', 'HOLD')
    sentiment_map = {
        'STRONG BUY': 'very_bullish',
        'BUY': 'bullish',
        'HOLD': 'neutral',
        'SELL': 'bearish',
        'STRONG SELL': 'very_bearish',
    }

    # Build entry
    symbol = analysis_data.get('symbol', 'BTC')
    entry = {
        'entry_type': entry_type,
        'title': f"{symbol} Market Analysis - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
        'content': ai_content,
        'summary': ai_content[:200] + '...' if len(ai_content) > 200 else ai_content,
        'symbols_analyzed': [symbol],
        'market_sentiment': sentiment_map.get(verdict, 'neutral'),
        'composite_score': analysis_data.get('verdict', {}).get('combined_score', 50),
        'data_sources': ['technical', 'regime', 'news', 'sentiment'],
        'sources_used': sources_used,
        'news_count': len(news),
        'indicators_used': ['RSI', 'MACD', 'VWAP', 'Ichimoku', 'Bollinger', 'EMA', 'ADX'],
        'ai_model': 'gemma4:latest',
        'ai_confidence': 0.75,
        'ai_reasoning': f"Analysis based on {analysis_data.get('data_points', 0)} data points, {len(news)} news articles from {len(sources_used)} sources",
        'key_findings': key_findings,
        'risks_identified': risks,
        'opportunities': opportunities,
        'tags': [symbol.lower(), entry_type, sentiment_map.get(verdict, 'neutral')],
    }

    # Market context snapshot
    context = {
        'btc_price': analysis_data.get('current_price', 0),
        'eth_price': 0,
        'btc_dominance': 54.0,
        'fear_greed_index': fear_greed.get('value', 50),
        'fear_greed_label': fear_greed.get('label', 'Neutral'),
        'total_market_cap': 0,
        'total_volume_24h': 0,
        'btc_trend': analysis_data.get('technical', {}).get('trend', {}).get('signal', 'neutral'),
        'btc_rsi': analysis_data.get('technical', {}).get('momentum', {}).get('rsi', 50),
        'btc_macd_signal': 'neutral',
        'news_sentiment_score': 50,
        'breaking_news_count': sum(1 for n in news if 'breaking' in n.get('title', '').lower()),
        'top_news_headlines': [{'title': n['title'], 'source': n['source'], 'icon': n.get('source_icon', '📰')} for n in news[:8]],
        'social_sentiment_score': fear_greed.get('value', 50),
        'funding_rate_avg': 0.0001,
    }

    return {
        'entry': entry,
        'context': context,
        'news': news,
        'sources_used': sources_used,
        'execution_time_ms': int((time.time() - start) * 1000),
    }


def _generate_fallback_content(analysis_data: Dict, fear_greed: Dict, news: List[Dict], sources_used: List[str]) -> str:
    """Generate fallback content when AI is unavailable."""
    symbol = analysis_data.get('symbol', 'BTC')
    price = analysis_data.get('current_price', 0)
    verdict = analysis_data.get('verdict', {})
    regime = analysis_data.get('regime', {}).get('composite', {})
    technical = analysis_data.get('technical', {})

    # Group news by source
    news_by_source = {}
    for n in news:
        src = n['source']
        if src not in news_by_source:
            news_by_source[src] = []
        news_by_source[src].append(n['title'])

    news_section = ""
    for source_name, titles in news_by_source.items():
        news_section += f"\n### {source_name}\n"
        for title in titles[:3]:
            news_section += f"- {title}\n"

    sources_section = "\n".join([f"- {s}" for s in sources_used])

    return f"""# {symbol} Market Analysis - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}

## Market Overview
BTC is currently trading at ${price:,.2f}. The market regime is {regime.get('zone', 'UNKNOWN')} with a composite score of {regime.get('score', 'N/A')}/100.

## Technical Analysis
- Overall Technical Score: {technical.get('overall_score', 'N/A')}/100
- Trend: {technical.get('trend', {}).get('signal', 'N/A')}
- RSI: {technical.get('momentum', {}).get('rsi', 'N/A')}
- VWAP: ${technical.get('vwap', {}).get('value', 0):,.2f}
- Ichimoku: {technical.get('ichimoku', {}).get('signal', 'N/A')}

## News & Sources Analysis
{news_section if news_section else "No recent news available."}

## Sentiment Analysis
Based on Alternative.me Fear & Greed Index: {fear_greed.get('value', 50)}/100 ({fear_greed.get('label', 'Neutral')})

## Verdict
Signal: {verdict.get('signal', 'HOLD')} (Combined Score: {verdict.get('combined_score', 'N/A')}/100)
Posture: {verdict.get('posture', 'MODERATE')}

## Key Levels
- Entry: ${analysis_data.get('position', {}).get('entry_price', 0):,.2f}
- Stop Loss: ${analysis_data.get('position', {}).get('stop_loss', 0):,.2f}
- Take Profit 1: ${analysis_data.get('position', {}).get('take_profits', [{}])[0].get('price', 0):,.2f}

## Sources Referenced
{sources_section}
"""


def _extract_findings(content: str, finding_type: str) -> List[str]:
    """Extract findings from AI-generated content."""
    findings = []
    lines = content.split('\n')

    in_section = False
    for line in lines:
        lower = line.lower()
        if finding_type == 'risk' and ('risk' in lower or 'threat' in lower or 'danger' in lower):
            in_section = True
            continue
        elif finding_type == 'opportunity' and ('opportunity' in lower or 'bullish' in lower or 'positive' in lower):
            in_section = True
            continue
        elif finding_type == 'finding' and ('finding' in lower or 'key' in lower or 'notable' in lower):
            in_section = True
            continue

        if in_section:
            if line.strip().startswith('-') or line.strip().startswith('*') or line.strip().startswith('•'):
                findings.append(line.strip().lstrip('-*• ').strip())
            elif line.strip() and not line.startswith('#'):
                if len(findings) < 5:
                    findings.append(line.strip())
                else:
                    break
            elif line.startswith('#'):
                in_section = False

    return findings[:5]
