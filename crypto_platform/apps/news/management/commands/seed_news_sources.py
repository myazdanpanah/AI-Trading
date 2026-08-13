"""Seed trusted news and social media sources into the database."""
from django.core.management.base import BaseCommand
from apps.news.models import NewsSource


# ═══════════════════════════════════════════════════════════════
# TRUSTED NEWS SOURCES (40+)
# ═══════════════════════════════════════════════════════════════
NEWS_SOURCES = [
    # Crypto News
    {'name': 'CoinDesk', 'url': 'https://www.coindesk.com/arc/outboundfeeds/rss/', 'source_type': 'rss', 'category': 'crypto_news', 'icon': '📰', 'reliability_score': 85, 'is_primary': True},
    {'name': 'CoinTelegraph', 'url': 'https://cointelegraph.com/rss', 'source_type': 'rss', 'category': 'crypto_news', 'icon': '📰', 'reliability_score': 80, 'is_primary': True},
    {'name': 'The Block', 'url': 'https://www.theblock.co/rss.xml', 'source_type': 'rss', 'category': 'crypto_news', 'icon': '📰', 'reliability_score': 85, 'is_primary': True},
    {'name': 'Decrypt', 'url': 'https://decrypt.co/feed', 'source_type': 'rss', 'category': 'crypto_news', 'icon': '📰', 'reliability_score': 75},
    {'name': 'Bitcoin Magazine', 'url': 'https://bitcoinmagazine.com/.rss/full/', 'source_type': 'rss', 'category': 'crypto_news', 'icon': '₿', 'reliability_score': 80},
    {'name': 'DL News', 'url': 'https://www.dlnews.com/rss/', 'source_type': 'rss', 'category': 'crypto_news', 'icon': '📰', 'reliability_score': 75},

    # Economics & Finance
    {'name': 'Bloomberg Markets', 'url': 'https://feeds.bloomberg.com/markets/news.rss', 'source_type': 'rss', 'category': 'economics', 'icon': '🏦', 'reliability_score': 95, 'is_primary': True},
    {'name': 'Financial Times', 'url': 'https://www.ft.com/rss/home', 'source_type': 'rss', 'category': 'economics', 'icon': '🏦', 'reliability_score': 95},
    {'name': 'Wall Street Journal', 'url': 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml', 'source_type': 'rss', 'category': 'economics', 'icon': '🏦', 'reliability_score': 95},
    {'name': 'CNBC Markets', 'url': 'https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258', 'source_type': 'rss', 'category': 'economics', 'icon': '🏦', 'reliability_score': 90},
    {'name': 'MarketWatch', 'url': 'https://feeds.marketwatch.com/marketwatch/topstories/', 'source_type': 'rss', 'category': 'economics', 'icon': '🏦', 'reliability_score': 85},
    {'name': 'Yahoo Finance', 'url': 'https://finance.yahoo.com/news/rssindex', 'source_type': 'rss', 'category': 'economics', 'icon': '🏦', 'reliability_score': 80},

    # Politics & Regulation
    {'name': 'Politico', 'url': 'https://rss.politico.com/economy.xml', 'source_type': 'rss', 'category': 'politics', 'icon': '⚖️', 'reliability_score': 90},
    {'name': 'The Hill', 'url': 'https://thehill.com/feed/', 'source_type': 'rss', 'category': 'politics', 'icon': '⚖️', 'reliability_score': 85},
    {'name': 'Coinbase Blog', 'url': 'https://blog.coinbase.com/feed', 'source_type': 'rss', 'category': 'regulation', 'icon': '📜', 'reliability_score': 80},
    {'name': 'SEC.gov', 'url': 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=8-K&dateb=&owner=include&count=40', 'source_type': 'rss', 'category': 'regulation', 'icon': '📜', 'reliability_score': 95},

    # Geopolitics
    {'name': 'BBC World', 'url': 'http://feeds.bbci.co.uk/news/world/rss.xml', 'source_type': 'rss', 'category': 'geopolitics', 'icon': '🌍', 'reliability_score': 90, 'is_primary': True},
    {'name': 'Al Jazeera', 'url': 'https://www.aljazeera.com/xml/rss/all.xml', 'source_type': 'rss', 'category': 'geopolitics', 'icon': '🌍', 'reliability_score': 85},
    {'name': 'The Guardian World', 'url': 'https://www.theguardian.com/world/rss', 'source_type': 'rss', 'category': 'geopolitics', 'icon': '🌍', 'reliability_score': 88},
    {'name': 'Foreign Policy', 'url': 'https://foreignpolicy.com/feed/', 'source_type': 'rss', 'category': 'geopolitics', 'icon': '🌍', 'reliability_score': 85},
    {'name': 'DW News', 'url': 'https://rss.dw.com/rdf/rss-en-all', 'source_type': 'rss', 'category': 'geopolitics', 'icon': '🌍', 'reliability_score': 85},

    # Conflict & Tensions
    {'name': 'War on the Rocks', 'url': 'https://warontherocks.com/feed/', 'source_type': 'rss', 'category': 'conflict', 'icon': '⚔️', 'reliability_score': 85},
    {'name': 'Crisis Group', 'url': 'https://www.crisisgroup.org/rss.xml', 'source_type': 'rss', 'category': 'conflict', 'icon': '⚔️', 'reliability_score': 90},
    {'name': 'Iran International', 'url': 'https://www.iranintl.com/en/rss', 'source_type': 'rss', 'category': 'conflict', 'icon': '🇮🇷', 'reliability_score': 80, 'is_primary': True},

    # Energy & Oil
    {'name': 'OilPrice.com', 'url': 'https://oilprice.com/rss/main', 'source_type': 'rss', 'category': 'energy', 'icon': '⛽', 'reliability_score': 85, 'is_primary': True},
    {'name': 'Rigzone', 'url': 'https://www.rigzone.com/news/rss/rigzone_latest.aspx', 'source_type': 'rss', 'category': 'energy', 'icon': '⛽', 'reliability_score': 80},
    {'name': 'EIA.gov', 'url': 'https://www.eia.gov/rss/todayinenergy.xml', 'source_type': 'rss', 'category': 'energy', 'icon': '⛽', 'reliability_score': 95},
    {'name': 'Energy Monitor', 'url': 'https://energymonitor.ai/feed/', 'source_type': 'rss', 'category': 'energy', 'icon': '⛽', 'reliability_score': 80},

    # Central Banks & Fed
    {'name': 'Federal Reserve', 'url': 'https://www.federalreserve.gov/feeds/press_all.xml', 'source_type': 'rss', 'category': 'central_banks', 'icon': '🏛️', 'reliability_score': 95, 'is_primary': True},
    {'name': 'ECB Press', 'url': 'https://www.ecb.europa.eu/rss/press.html', 'source_type': 'rss', 'category': 'central_banks', 'icon': '🏛️', 'reliability_score': 95},

    # Commodities & Gold
    {'name': 'Investing Commodities', 'url': 'https://www.investing.com/rss/news_25.rss', 'source_type': 'rss', 'category': 'commodities', 'icon': '🥇', 'reliability_score': 80},

    # Technology
    {'name': 'TechCrunch', 'url': 'https://techcrunch.com/feed/', 'source_type': 'rss', 'category': 'technology', 'icon': '💻', 'reliability_score': 85},
    {'name': 'Ars Technica', 'url': 'https://feeds.arstechnica.com/arstechnica/index', 'source_type': 'rss', 'category': 'technology', 'icon': '💻', 'reliability_score': 85},
]


# ═══════════════════════════════════════════════════════════════
# SOCIAL MEDIA / X ACCOUNTS (30+)
# ═══════════════════════════════════════════════════════════════
SOCIAL_SOURCES = [
    # X/Twitter - Crypto Analysts
    {'name': '@CryptoCapo_', 'url': 'https://x.com/CryptoCapo_', 'source_type': 'twitter', 'category': 'twitter_analyst', 'icon': '🐦', 'reliability_score': 70, 'is_primary': True},
    {'name': '@PlanB_', 'url': 'https://x.com/100trillionUSD', 'source_type': 'twitter', 'category': 'twitter_analyst', 'icon': '₿', 'reliability_score': 75, 'is_primary': True},
    {'name': '@WillyWoo', 'url': 'https://x.com/woonomic', 'source_type': 'twitter', 'category': 'twitter_analyst', 'icon': '📊', 'reliability_score': 75},
    {'name': '@CryptoHayes', 'url': 'https://x.com/CryptoHayes', 'source_type': 'twitter', 'category': 'twitter_analyst', 'icon': '🐦', 'reliability_score': 70},
    {'name': '@cobie', 'url': 'https://x.com/caborneto', 'source_type': 'twitter', 'category': 'twitter_analyst', 'icon': '🐦', 'reliability_score': 70},
    {'name': '@Pentosh1', 'url': 'https://x.com/Pentosh1', 'source_type': 'twitter', 'category': 'twitter_analyst', 'icon': '📈', 'reliability_score': 70},
    {'name': '@BluntzCapital', 'url': 'https://x.com/Bluntz_Capital', 'source_type': 'twitter', 'category': 'twitter_analyst', 'icon': '🐦', 'reliability_score': 70},
    {'name': '@CryptoISO', 'url': 'https://x.com/CryptoISO', 'source_type': 'twitter', 'category': 'twitter_analyst', 'icon': '🐦', 'reliability_score': 65},

    # X/Twitter - Breaking News
    {'name': '@WatcherGuru', 'url': 'https://x.com/WatcherGuru', 'source_type': 'twitter', 'category': 'twitter_news', 'icon': '📢', 'reliability_score': 80, 'is_primary': True},
    {'name': '@BitcoinMagazine', 'url': 'https://x.com/BitcoinMagazine', 'source_type': 'twitter', 'category': 'twitter_news', 'icon': '📰', 'reliability_score': 85},
    {'name': '@coindesk', 'url': 'https://x.com/coindesk', 'source_type': 'twitter', 'category': 'twitter_news', 'icon': '📰', 'reliability_score': 85},
    {'name': '@tier10k', 'url': 'https://x.com/tier10k', 'source_type': 'twitter', 'category': 'twitter_news', 'icon': '⚡', 'reliability_score': 75},
    {'name': '@WhaleAlert', 'url': 'https://x.com/WhaleAlert', 'source_type': 'twitter', 'category': 'twitter_news', 'icon': '🐋', 'reliability_score': 80, 'is_primary': True},
    {'name': '@unusual_whales', 'url': 'https://x.com/unusual_whales', 'source_type': 'twitter', 'category': 'twitter_news', 'icon': '🐟', 'reliability_score': 75},

    # X/Twitter - Geopolitics
    {'name': '@sentdefender', 'url': 'https://x.com/sentdefender', 'source_type': 'twitter', 'category': 'twitter_geopolitics', 'icon': '⚔️', 'reliability_score': 80, 'is_primary': True},
    {'name': '@OSINTdefender', 'url': 'https://x.com/OSINTdefender', 'source_type': 'twitter', 'category': 'twitter_geopolitics', 'icon': '🔍', 'reliability_score': 75},
    {'name': '@spectatorindex', 'url': 'https://x.com/spectatorindex', 'source_type': 'twitter', 'category': 'twitter_geopolitics', 'icon': '📰', 'reliability_score': 75},
    {'name': '@BNONews', 'url': 'https://x.com/BNONews', 'source_type': 'twitter', 'category': 'twitter_geopolitics', 'icon': '📢', 'reliability_score': 80},
    {'name': '@LiveSquawk', 'url': 'https://x.com/LiveSquawk', 'source_type': 'twitter', 'category': 'twitter_geopolitics', 'icon': '📡', 'reliability_score': 80},
    {'name': '@firstsquawk', 'url': 'https://x.com/firstsquawk', 'source_type': 'twitter', 'category': 'twitter_geopolitics', 'icon': '⚡', 'reliability_score': 75},
    {'name': '@FinancialJuice', 'url': 'https://x.com/Financialjuice1', 'source_type': 'twitter', 'category': 'twitter_geopolitics', 'icon': '📰', 'reliability_score': 75},
    {'name': '@disclosetv', 'url': 'https://x.com/disclosetv', 'source_type': 'twitter', 'category': 'twitter_geopolitics', 'icon': '📺', 'reliability_score': 70},

    # X/Twitter - Iran Focus
    {'name': '@IranIntl', 'url': 'https://x.com/IranIntl', 'source_type': 'twitter', 'category': 'twitter_geopolitics', 'icon': '🇮🇷', 'reliability_score': 80, 'is_primary': True},
    {'name': '@IranIntl_En', 'url': 'https://x.com/IranIntl_En', 'source_type': 'twitter', 'category': 'twitter_geopolitics', 'icon': '🇮🇷', 'reliability_score': 80},

    # X/Twitter - Macro & Gold
    {'name': '@GoldTelegraph_', 'url': 'https://x.com/GoldTelegraph_', 'source_type': 'twitter', 'category': 'twitter_macro', 'icon': '🥇', 'reliability_score': 70},
    {'name': '@SantiagoAuFund', 'url': 'https://x.com/SantiagoAuFund', 'source_type': 'twitter', 'category': 'twitter_macro', 'icon': '🥇', 'reliability_score': 70},

    # Reddit
    {'name': 'r/cryptocurrency', 'url': 'https://www.reddit.com/r/cryptocurrency/.rss', 'source_type': 'reddit', 'category': 'reddit', 'icon': '📰', 'reliability_score': 65},
    {'name': 'r/bitcoin', 'url': 'https://www.reddit.com/r/bitcoin/.rss', 'source_type': 'reddit', 'category': 'reddit', 'icon': '📰', 'reliability_score': 70},
    {'name': 'r/CryptoMarkets', 'url': 'https://www.reddit.com/r/CryptoMarkets/.rss', 'source_type': 'reddit', 'category': 'reddit', 'icon': '📊', 'reliability_score': 60},

    # YouTube
    {'name': 'Coin Bureau', 'url': 'https://www.youtube.com/feeds/videos.xml?channel_id=UCqqJQcXSS1SCa_pjTggmeZQ', 'source_type': 'youtube', 'category': 'youtube', 'icon': '📺', 'reliability_score': 80, 'is_primary': True},
    {'name': 'Coffeezilla', 'url': 'https://www.youtube.com/feeds/videos.xml?channel_id=UCFbMTIlLUj5N6v3yztqitmw', 'source_type': 'youtube', 'category': 'youtube', 'icon': '📺', 'reliability_score': 75},
    {'name': 'Ivan on Tech', 'url': 'https://www.youtube.com/feeds/videos.xml?channel_id=UC_cKlfpE530YZ2uppiQt3ng', 'source_type': 'youtube', 'category': 'youtube', 'icon': '📺', 'reliability_score': 70},
    {'name': 'Real Vision', 'url': 'https://www.youtube.com/feeds/videos.xml?channel_id=UCN4mY17MU8Axj1eEIb17h6g', 'source_type': 'youtube', 'category': 'youtube', 'icon': '📺', 'reliability_score': 80},

    # Telegram
    {'name': 'Crypto Telegram', 'url': 'https://t.me/s/cryptocurrencynews', 'source_type': 'telegram', 'category': 'telegram', 'icon': '💬', 'reliability_score': 55},
]


class Command(BaseCommand):
    help = 'Seed trusted news and social media sources into the database'

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        self.stdout.write('Seeding news sources...')

        for source_data in NEWS_SOURCES + SOCIAL_SOURCES:
            source, created = NewsSource.objects.update_or_create(
                name=source_data['name'],
                defaults=source_data,
            )
            if created:
                created_count += 1
                self.stdout.write(f'  + {source_data["name"]}')
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Created: {created_count}, Updated: {updated_count}, '
            f'Total: {NewsSource.objects.count()} sources'
        ))
