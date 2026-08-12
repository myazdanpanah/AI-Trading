#!/usr/bin/env python
"""Test candlestick analysis skill."""
import sys
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.path.insert(0, '/c/Trading')

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'crypto_platform.settings.local'

import django
django.setup()

from apps.trading_skills.services.candlestick_skill import CandlestickSkill
import urllib.request
import json

# Fetch BTC data
url = 'https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=60'
req = urllib.request.Request(url)
data = json.loads(urllib.request.urlopen(req).read())
closes = [p[1] for p in data['prices']]

# Calculate approximate highs and lows
import numpy as np
np.random.seed(42)
highs = [c * (1 + abs(np.random.normal(0, 0.015))) for c in closes]
lows = [c * (1 - abs(np.random.normal(0, 0.015))) for c in closes]

# Run analysis
result = CandlestickSkill.analyze(closes, highs, lows)

print("=" * 60)
print("CANDLESTICK ANALYSIS - BTC/USD")
print("=" * 60)

print("\n📊 T.A.E. Framework Analysis:")
print(f"  Trend Bias: {result['bias'].upper()}")
print(f"  MA Value: ${result['trend']['ma_value']:,.2f}")
print(f"  Price vs MA: {result['trend']['price_vs_ma_pct']:+.2f}%")

print(f"\n🎯 Area of Value:")
aov = result['area_of_value']
if aov.get('nearest_support'):
    print(f"  Support: ${aov['nearest_support']:,.2f} ({aov['dist_to_support_pct']:.1f}% away)")
if aov.get('nearest_resistance'):
    print(f"  Resistance: ${aov['nearest_resistance']:,.2f} ({aov['dist_to_resistance_pct']:.1f}% away)")
print(f"  In Value Zone: {'Yes' if aov.get('in_value_zone') else 'No'}")

print(f"\n🕯️ Patterns Detected: {len(result['patterns'])}")
for p in result['patterns'][-5:]:
    print(f"  - {p['name']}: {p['direction'].upper()} ({p['confidence']:.0%})")
    print(f"    Entry: ${p['entry']:,.2f} | SL: ${p['stop_loss']:,.2f} | TP: ${p['take_profit']:,.2f}")
    print(f"    R:R = {p['risk_reward']:.2f}")

print(f"\n📈 Signals Generated: {len(result['signals'])}")
for s in result['signals'][-3:]:
    print(f"  - {s['type']} {s['pattern']} (strength: {s['strength']:.0%})")
    print(f"    Trend Aligned: {'✓' if s['trend_aligned'] else '✗'} | At Value: {'✓' if s['at_area_of_value'] else '✗'}")

print(f"\n🏆 Overall Score:")
score = result['overall_score']
print(f"  Trend: {score['trend_score']:.1f}")
print(f"  Area of Value: {score['aov_score']:.1f}")
print(f"  Pattern: {score['pattern_score']:.1f}")
print(f"  COMBINED: {score['overall']:.1f}/100")

print(f"\n📝 Summary:")
print(f"  {result['summary']}")
print("=" * 60)
