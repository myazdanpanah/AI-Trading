"""AI Journal Writer - Generates journal entries from market data and analysis."""
import json
import time
import urllib.request
from datetime import datetime, timezone
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# News sources (RSS feeds)
NEWS_FEEDS = {
    'coindesk': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
    'cointelegraph': 'https://cointelegraph.com/rss',
    'decrypt': 'https://decrypt.co/feed',
    'theblock': 'https://www.theblock.co/rss.xml',
    'bitcoin_magazine': 'https://bitcoinmagazine.com/feed',
}


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
            'timestamp': entry['timestamp'],
        }
    except Exception as e:
        logger.warning(f"Failed to fetch Fear & Greed: {e}")
        return {'value': 50, 'label': 'Neutral', 'timestamp': str(int(time.time()))}


def fetch_news_headlines(limit: int = 10) -> List[Dict]:
    """Fetch latest crypto news headlines from RSS feeds."""
    try:
        import feedparser
        headlines = []

        for source, url in NEWS_FEEDS.items():
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:3]:  # Top 3 from each source
                    headlines.append({
                        'title': entry.get('title', ''),
                        'source': source,
                        'url': entry.get('link', ''),
                        'published': entry.get('published', ''),
                        'summary': entry.get('summary', '')[:200],
                    })
            except Exception:
                continue

            if len(headlines) >= limit:
                break

        return headlines[:limit]
    except Exception as e:
        logger.warning(f"Failed to fetch news: {e}")
        return []


def generate_market_summary(analysis_data: Dict, news: List[Dict], fear_greed: Dict) -> str:
    """Generate a comprehensive market summary prompt for the LLM."""
    price = analysis_data.get('current_price', 0)
    regime = analysis_data.get('regime', {}).get('composite', {})
    technical = analysis_data.get('technical', {})
    verdict = analysis_data.get('verdict', {})

    news_text = "\n".join([
        f"- [{h['source']}] {h['title']}" for h in news[:5]
    ]) if news else "No recent news available."

    prompt = f"""You are an expert crypto market analyst writing a journal entry.

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

Recent News:
{news_text}

Write a professional journal entry with:
1. MARKET OVERVIEW: Current state of BTC and crypto market
2. TECHNICAL ANALYSIS: Key indicator readings and what they mean
3. NEWS IMPACT: How recent news is affecting the market
4. SENTIMENT ANALYSIS: What the Fear & Greed index and social signals indicate
5. KEY RISKS: What could go wrong
6. OPPORTUNITIES: What looks promising
7. OUTLOOK: Your 24-48 hour market outlook
8. ACTION ITEMS: Specific things to watch for

Write in a professional, analytical tone. Be specific with numbers and levels.
Keep it concise but thorough (500-800 words)."""

    return prompt


def call_ollama(prompt: str, model: str = 'gemma4:latest') -> Optional[str]:
    """Call Ollama API for text generation."""
    try:
        data = json.dumps({
            'model': model,
            'messages': [{'role': 'user', 'content': prompt}],
            'stream': False,
            'options': {'temperature': 0.7, 'num_predict': 2000},
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


def generate_journal_entry(analysis_data: Dict, entry_type: str = 'market_analysis') -> Dict:
    """
    Generate a complete journal entry using AI.

    Args:
        analysis_data: Full analysis from /api/skills/full-analysis/
        entry_type: Type of journal entry

    Returns:
        Dict with journal entry data ready for database storage
    """
    start = time.time()

    # Fetch supporting data
    fear_greed = fetch_fear_greed_index()
    news = fetch_news_headlines(limit=10)

    # Generate AI content
    prompt = generate_market_summary(analysis_data, news, fear_greed)
    ai_content = call_ollama(prompt)

    if not ai_content:
        # Fallback: generate structured entry without AI
        ai_content = _generate_fallback_content(analysis_data, fear_greed, news)

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
        'news_count': len(news),
        'indicators_used': ['RSI', 'MACD', 'VWAP', 'Ichimoku', 'Bollinger', 'EMA', 'ADX'],
        'ai_model': 'gemma4:latest',
        'ai_confidence': 0.75,
        'ai_reasoning': f"Analysis based on {analysis_data.get('data_points', 0)} data points with regime score {analysis_data.get('regime', {}).get('composite', {}).get('score', 'N/A')}",
        'key_findings': key_findings,
        'risks_identified': risks,
        'opportunities': opportunities,
        'tags': [symbol.lower(), entry_type, sentiment_map.get(verdict, 'neutral')],
    }

    # Market context snapshot
    prices = analysis_data
    context = {
        'btc_price': prices.get('current_price', 0),
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
        'top_news_headlines': [{'title': n['title'], 'source': n['source']} for n in news[:5]],
        'social_sentiment_score': fear_greed.get('value', 50),
        'funding_rate_avg': 0.0001,
    }

    return {
        'entry': entry,
        'context': context,
        'news': news,
        'execution_time_ms': int((time.time() - start) * 1000),
    }


def _generate_fallback_content(analysis_data: Dict, fear_greed: Dict, news: List[Dict]) -> str:
    """Generate fallback content when AI is unavailable."""
    symbol = analysis_data.get('symbol', 'BTC')
    price = analysis_data.get('current_price', 0)
    verdict = analysis_data.get('verdict', {})
    regime = analysis_data.get('regime', {}).get('composite', {})
    technical = analysis_data.get('technical', {})

    news_section = ""
    if news:
        news_section = "\n\nRecent Headlines:\n" + "\n".join([
            f"- [{n['source']}] {n['title']}" for n in news[:5]
        ])

    return f"""# {symbol} Market Analysis - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}

## Market Overview
BTC is currently trading at ${price:,.2f}. The market regime is {regime.get('zone', 'UNKNOWN')} with a composite score of {regime.get('score', 'N/A')}/100.

## Technical Analysis
- Overall Technical Score: {technical.get('overall_score', 'N/A')}/100
- Trend: {technical.get('trend', {}).get('signal', 'N/A')}
- RSI: {technical.get('momentum', {}).get('rsi', 'N/A')}
- VWAP: ${technical.get('vwap', {}).get('value', 0):,.2f}
- Ichimoku: {technical.get('ichimoku', {}).get('signal', 'N/A')}

## Sentiment
Fear & Greed Index: {fear_greed.get('value', 50)}/100 ({fear_greed.get('label', 'Neutral')})

## Verdict
Signal: {verdict.get('signal', 'HOLD')} (Combined Score: {verdict.get('combined_score', 'N/A')}/100)
Posture: {verdict.get('posture', 'MODERATE')}
{news_section}

## Key Levels
- Entry: ${analysis_data.get('position', {}).get('entry_price', 0):,.2f}
- Stop Loss: ${analysis_data.get('position', {}).get('stop_loss', 0):,.2f}
- Take Profit 1: ${analysis_data.get('position', {}).get('take_profits', [{}])[0].get('price', 0):,.2f}
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
