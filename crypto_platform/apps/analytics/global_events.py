"""Global event models for macroeconomic and geopolitical events."""
import uuid
from django.db import models


class EconomicEvent(models.Model):
    """Economic calendar events (CPI, PPI, GDP, FOMC, etc.)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    event_type = models.CharField(
        max_length=30,
        choices=[
            ('cpi', 'Consumer Price Index'),
            ('ppi', 'Producer Price Index'),
            ('gdp', 'Gross Domestic Product'),
            ('interest_rate', 'Interest Rate Decision'),
            ('fomc', 'FOMC Meeting'),
            ('employment', 'Employment Data'),
            ('nonfarm', 'Non-Farm Payrolls'),
            ('retail_sales', 'Retail Sales'),
            ('pmi', 'Purchasing Managers Index'),
            ('consumer_sentiment', 'Consumer Sentiment'),
            ('inflation', 'Inflation Data'),
            ('other', 'Other Economic Event'),
        ]
    )
    country = models.CharField(max_length=10, default='US')  # US, EU, JP, CN, etc.
    impact_level = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ],
        default='medium'
    )
    scheduled_date = models.DateTimeField(db_index=True)
    actual_value = models.CharField(max_length=100, blank=True)
    forecast_value = models.CharField(max_length=100, blank=True)
    previous_value = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=20, default='%')
    source = models.CharField(max_length=100, default='official')
    is_released = models.BooleanField(default=False)
    market_impact = models.JSONField(default=dict)  # {direction: bullish/bearish, severity: 0-100}
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'economic event'
        verbose_name_plural = 'economic events'
        db_table = 'economic_events'
        ordering = ['scheduled_date']

    def __str__(self):
        return f"{self.name} - {self.scheduled_date}"


class RegulatoryEvent(models.Model):
    """Regulatory events (SEC, ETF, exchange regulations)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300)
    event_type = models.CharField(
        max_length=30,
        choices=[
            ('sec_decision', 'SEC Decision'),
            ('etf_approval', 'ETF Approval'),
            ('etf_rejection', 'ETF Rejection'),
            ('exchange_regulation', 'Exchange Regulation'),
            ('crypto_ban', 'Crypto Ban'),
            ('crypto_legalization', 'Crypto Legalization'),
            ('tax_regulation', 'Tax Regulation'),
            ('compliance', 'Compliance Requirement'),
            ('enforcement', 'Enforcement Action'),
            ('other', 'Other Regulatory Event'),
        ]
    )
    jurisdiction = models.CharField(max_length=50)  # US, EU, UK, etc.
    affected_assets = models.JSONField(default=list)  # ['BTC', 'ETH']
    severity = models.IntegerField(default=50)  # 0-100
    direction = models.CharField(
        max_length=10,
        choices=[
            ('bullish', 'Bullish'),
            ('neutral', 'Neutral'),
            ('bearish', 'Bearish'),
        ],
        default='neutral'
    )
    source = models.CharField(max_length=100)
    source_url = models.URLField(blank=True)
    summary = models.TextField(blank=True)
    event_date = models.DateTimeField(db_index=True)
    effective_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'regulatory event'
        verbose_name_plural = 'regulatory events'
        db_table = 'regulatory_events'
        ordering = ['-event_date']

    def __str__(self):
        return f"{self.title} - {self.jurisdiction}"


class GeopoliticalEvent(models.Model):
    """Geopolitical events (war, sanctions, elections)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300)
    event_type = models.CharField(
        max_length=30,
        choices=[
            ('war', 'War/Conflict'),
            ('sanctions', 'Sanctions'),
            ('election', 'Election'),
            ('government_decision', 'Government Decision'),
            ('diplomatic', 'Diplomatic Event'),
            ('trade_war', 'Trade War'),
            ('energy_crisis', 'Energy Crisis'),
            ('pandemic', 'Pandemic/Health'),
            ('natural_disaster', 'Natural Disaster'),
            ('other', 'Other Geopolitical Event'),
        ]
    )
    region = models.CharField(max_length=50)  # Global, US, Asia, Europe, etc.
    affected_assets = models.JSONField(default=list)
    severity = models.IntegerField(default=50)  # 0-100
    direction = models.CharField(
        max_length=10,
        choices=[
            ('bullish', 'Bullish'),
            ('neutral', 'Neutral'),
            ('bearish', 'Bearish'),
        ],
        default='neutral'
    )
    source = models.CharField(max_length=100)
    source_url = models.URLField(blank=True)
    summary = models.TextField()
    event_date = models.DateTimeField(db_index=True)
    expected_duration = models.CharField(max_length=50, default='short')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'geopolitical event'
        verbose_name_plural = 'geopolitical events'
        db_table = 'geopolitical_events'
        ordering = ['-event_date']

    def __str__(self):
        return f"{self.title} - {self.region}"


class BlockchainEvent(models.Model):
    """Blockchain-specific events (forks, upgrades, hacks)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300)
    event_type = models.CharField(
        max_length=30,
        choices=[
            ('hard_fork', 'Hard Fork'),
            ('soft_fork', 'Soft Fork'),
            ('upgrade', 'Network Upgrade'),
            ('token_unlock', 'Token Unlock'),
            ('token_burn', 'Token Burn'),
            ('hack', 'Security Hack'),
            ('exploit', 'Exploit'),
            ('bridge_hack', 'Bridge Hack'),
            ('partnership', 'Partnership'),
            ('listing', 'Exchange Listing'),
            ('delisting', 'Exchange Delisting'),
            ('other', 'Other Blockchain Event'),
        ]
    )
    blockchain = models.CharField(max_length=50)  # Bitcoin, Ethereum, Solana, etc.
    affected_assets = models.JSONField(default=list)
    severity = models.IntegerField(default=50)  # 0-100
    direction = models.CharField(
        max_length=10,
        choices=[
            ('bullish', 'Bullish'),
            ('neutral', 'Neutral'),
            ('bearish', 'Bearish'),
        ],
        default='neutral'
    )
    source = models.CharField(max_length=100)
    source_url = models.URLField(blank=True)
    summary = models.TextField()
    event_date = models.DateTimeField(db_index=True)
    amount_usd = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)  # For hacks, burns, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'blockchain event'
        verbose_name_plural = 'blockchain events'
        db_table = 'blockchain_events'
        ordering = ['-event_date']

    def __str__(self):
        return f"{self.title} - {self.blockchain}"


class GlobalEventImpact(models.Model):
    """Tracks impact of events on crypto markets."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(
        max_length=30,
        choices=[
            ('economic', 'Economic Event'),
            ('regulatory', 'Regulatory Event'),
            ('geopolitical', 'Geopolitical Event'),
            ('blockchain', 'Blockchain Event'),
        ]
    )
    event_id = models.UUIDField()  # References the specific event
    impact_score = models.IntegerField(default=0)  # -100 to 100
    market_reaction = models.JSONField(default=dict)  # Price/volume changes
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'global event impact'
        verbose_name_plural = 'global event impacts'
        db_table = 'global_event_impacts'

    def __str__(self):
        return f"{self.event_type} impact - {self.event_id}"