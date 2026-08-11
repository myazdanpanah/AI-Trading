"""Seed default FactorWeight and RiskProfile records."""
from django.db import migrations


def create_default_factor_weights(apps, schema_editor):
    """Create default factor weights for signal generation."""
    FactorWeight = apps.get_model('signals', 'FactorWeight')
    
    weights = [
        {
            'name': 'technical',
            'weight': 0.30,
            'description': 'Technical analysis indicators (RSI, MACD, trends, S/R levels)',
            'min_score': 0,
            'max_score': 100,
        },
        {
            'name': 'sentiment',
            'weight': 0.20,
            'description': 'Market sentiment (Fear & Greed, social, whale activity)',
            'min_score': 0,
            'max_score': 100,
        },
        {
            'name': 'news',
            'weight': 0.15,
            'description': 'News analysis (sentiment, impact, breaking news)',
            'min_score': 0,
            'max_score': 100,
        },
        {
            'name': 'ai',
            'weight': 0.20,
            'description': 'AI model predictions and consensus',
            'min_score': 0,
            'max_score': 100,
        },
        {
            'name': 'macro',
            'weight': 0.15,
            'description': 'Macroeconomic factors (BTC correlation, market regime, DXY)',
            'min_score': 0,
            'max_score': 100,
        },
    ]
    
    for weight_data in weights:
        FactorWeight.objects.get_or_create(
            name=weight_data['name'],
            defaults=weight_data,
        )


def create_default_risk_profiles(apps, schema_editor):
    """Create default risk management profiles."""
    RiskProfile = apps.get_model('signals', 'RiskProfile')
    
    profiles = [
        {
            'name': 'Conservative',
            'max_portfolio_risk': 2.0,
            'max_position_size': 5.0,
            'max_correlated_positions': 2,
            'max_drawdown': 5.0,
            'risk_per_trade': 0.5,
            'use_kelly_criterion': False,
            'kelly_fraction': 0.25,
        },
        {
            'name': 'Moderate',
            'max_portfolio_risk': 4.0,
            'max_position_size': 10.0,
            'max_correlated_positions': 3,
            'max_drawdown': 10.0,
            'risk_per_trade': 1.0,
            'use_kelly_criterion': False,
            'kelly_fraction': 0.25,
        },
        {
            'name': 'Aggressive',
            'max_portfolio_risk': 6.0,
            'max_position_size': 15.0,
            'max_correlated_positions': 4,
            'max_drawdown': 15.0,
            'risk_per_trade': 2.0,
            'use_kelly_criterion': True,
            'kelly_fraction': 0.50,
        },
    ]
    
    for profile_data in profiles:
        RiskProfile.objects.get_or_create(
            name=profile_data['name'],
            defaults=profile_data,
        )


def reverse_func(apps, schema_editor):
    """Reverse migration - remove seeded data."""
    FactorWeight = apps.get_model('signals', 'FactorWeight')
    RiskProfile = apps.get_model('signals', 'RiskProfile')
    
    FactorWeight.objects.filter(name__in=['technical', 'sentiment', 'news', 'ai', 'macro']).delete()
    RiskProfile.objects.filter(name__in=['Conservative', 'Moderate', 'Aggressive']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_factor_weights, reverse_func),
        migrations.RunPython(create_default_risk_profiles, reverse_func),
    ]
