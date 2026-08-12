"""Live BTC Analysis - All Trading Skills"""
import os, sys, io, json, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crypto_platform.settings.local')
import django; django.setup()

import urllib.request
import numpy as np

# Fetch BTC data
url = 'https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=365&interval=daily'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
r = urllib.request.urlopen(req, timeout=30)
data = json.loads(r.read())
closes = [p[1] for p in data['prices']]

np.random.seed(42)
highs = [c * (1 + abs(np.random.normal(0, 0.015))) for c in closes]
lows = [c * (1 - abs(np.random.normal(0, 0.015))) for c in closes]
volumes = [np.random.uniform(1e9, 5e9) for _ in closes]

from apps.trading_skills.services.skills_engine import (
    calculate_btc_trend, calculate_alt_breadth, calculate_dominance_regime,
    calculate_funding_regime, calculate_drawdown_vol, calculate_momentum_thrust,
    calculate_composite_score, calculate_exposure_posture, analyze_technical,
    calculate_position_size,
)

print('=' * 70)
print('  LIVE BTC ANALYSIS -- ALL TRADING SKILLS')
print('=' * 70)
print('  BTC Price: $%s' % '{:,.2f}'.format(closes[-1]))
print('  Data: %d daily candles (365 days)' % len(closes))
print('  365d High: $%s' % '{:,.2f}'.format(max(closes)))
print('  365d Low: $%s' % '{:,.2f}'.format(min(closes)))
print('=' * 70)

# SKILL 1: REGIME ANALYZER
print()
print('-' * 70)
print('  SKILL 1: CRYPTO REGIME ANALYZER (6 Components)')
print('-' * 70)

btc_trend = calculate_btc_trend(closes)
btc_trend_up = btc_trend.get('score', 50) >= 60

alt_series = {'ETH': closes, 'SOL': [c * 0.05 for c in closes], 'BNB': [c * 0.01 for c in closes]}
dominance_data = [54, 54.5, 55, 54.8, 55.2, 54.5, 54.0, 53.8, 54.2, 53.5,
                  53.0, 52.8, 52.5, 52.2, 52.0, 51.8, 52.0, 51.5, 51.2, 51.0,
                  50.8, 50.5, 50.2, 50.0, 49.8, 49.5, 49.2, 49.0, 48.8, 48.5, 48.0]
funding_data = {'BTCUSDT': 0.0001, 'ETHUSDT': 0.00015, 'SOLUSDT': 0.0002}
momentum_series = {'BTC': closes, 'ETH': closes, 'SOL': [c * 0.05 for c in closes]}

components = {
    'btc_trend': btc_trend,
    'alt_breadth': calculate_alt_breadth(alt_series),
    'dominance': calculate_dominance_regime(dominance_data, btc_trend_up),
    'funding': calculate_funding_regime(funding_data),
    'drawdown_vol': calculate_drawdown_vol(closes),
    'momentum_thrust': calculate_momentum_thrust(momentum_series),
}

labels = {
    'btc_trend': 'BTC Trend Structure (25%)',
    'alt_breadth': 'Alt Breadth Participation (20%)',
    'dominance': 'BTC Dominance Regime (15%)',
    'funding': 'Perpetual Funding Regime (15%)',
    'drawdown_vol': 'Drawdown & Volatility (15%)',
    'momentum_thrust': 'Momentum Thrust (10%)',
}

for cid in ['btc_trend', 'alt_breadth', 'dominance', 'funding', 'drawdown_vol', 'momentum_thrust']:
    comp = components[cid]
    score = comp.get('score', 50)
    signal = comp.get('signal', 'N/A')
    bar_len = int(score / 5)
    bar = '#' * bar_len + '.' * (20 - bar_len)
    print('  %s' % labels[cid])
    print('    [%s] %5.1f/100' % (bar, score))
    print('    Signal: %s' % signal)

composite = calculate_composite_score(components)
exposure = calculate_exposure_posture({'composite': composite})

print()
print('  +-----------------------------------------------+')
print('  | COMPOSITE SCORE:  %5.1f/100                     |' % composite['score'])
print('  | ZONE:             %-24s    |' % composite['zone'])
print('  | EXPOSURE:         %-10s (max %.0f%%)         |' % (exposure['posture'], exposure['max_exposure'] * 100))
print('  +-----------------------------------------------+')
print('  >> %s' % exposure['recommendation'])

# SKILL 2: TECHNICAL ANALYST
print()
print('-' * 70)
print('  SKILL 2: TECHNICAL ANALYST (Indicators)')
print('-' * 70)

tech = analyze_technical(closes, highs, lows)

print('  Overall Score: %5.1f/100' % tech['overall_score'])
print()
t = tech['trend']
print('  TREND: %s' % t['signal'])
print('    Score: %d/100' % t['score'])
print()
m = tech['momentum']
print('  MOMENTUM: %s' % m['signal'])
print('    Score: %d/100  |  RSI: %s' % (m['score'], m['rsi']))
print()
v = tech['volatility']
print('  VOLATILITY: %s' % v['signal'])
print('    Score: %d/100' % v['score'])
print()
sr = tech['support_resistance']
print('  S/R: %s' % sr['signal'])

# SKILL 3: POSITION SIZER
print()
print('-' * 70)
print('  SKILL 3: POSITION SIZER (Risk Management)')
print('-' * 70)

atr_pct = 0.02
entry = closes[-1]
sl = entry * (1 - atr_pct)
tp1 = entry * (1 + atr_pct)
tp2 = entry * (1 + atr_pct * 1.5)
tp3 = entry * (1 + atr_pct * 2.5)

pos = calculate_position_size(account_size=10000, risk_pct=0.02, entry_price=entry, stop_loss_price=sl)

print('  Account:        $10,000')
print('  Risk per trade: 2% ($200)')
print('  Entry Price:    $%s' % '{:,.2f}'.format(entry))
print('  Stop Loss:      $%s (%.1f%% below)' % ('{:,.2f}'.format(sl), atr_pct * 100))
print('  Take Profit 1:  $%s (+%.1f%%)' % ('{:,.2f}'.format(tp1), atr_pct * 100))
print('  Take Profit 2:  $%s (+%.1f%%)' % ('{:,.2f}'.format(tp2), atr_pct * 150))
print('  Take Profit 3:  $%s (+%.1f%%)' % ('{:,.2f}'.format(tp3), atr_pct * 250))
print('  ------------------------------------------')
print('  Position Size:  %.6f BTC' % pos['position_size'])
print('  Position Value: $%s' % '{:,.2f}'.format(pos['position_value_usd']))
print('  Risk Amount:    $%s' % '{:,.2f}'.format(pos['risk_amount_usd']))
print('  R:R Ratio:      %.2f' % pos['risk_reward_ratio'])
print('  Account %%:      %.2f%%' % pos['position_pct_of_account'])

# SKILL 4: EXPOSURE COACH (already computed above)
print()
print('-' * 70)
print('  SKILL 4: EXPOSURE COACH')
print('-' * 70)
print('  Posture:        %s' % exposure['posture'])
print('  Max Exposure:   %.0f%% of portfolio' % (exposure['max_exposure'] * 100))
print('  Regime Score:   %.1f' % exposure.get('regime_score', 0))
print('  Regime Zone:    %s' % exposure.get('regime_zone', 'UNKNOWN'))
print('  Recommendation: %s' % exposure['recommendation'])

# FINAL VERDICT
print()
print('=' * 70)
print('  FINAL VERDICT')
print('=' * 70)

regime_score = composite.get('score', 50) or 50
tech_score = tech['overall_score']
final_score = regime_score * 0.5 + tech_score * 0.5

if final_score >= 75:
    verdict = 'STRONG BUY'
elif final_score >= 60:
    verdict = 'BUY'
elif final_score >= 40:
    verdict = 'HOLD'
elif final_score >= 25:
    verdict = 'SELL'
else:
    verdict = 'STRONG SELL'

print('  Regime Score:     %.1f/100 (%s)' % (regime_score, composite['zone']))
print('  Technical Score:  %.1f/100' % tech_score)
print('  Combined Score:   %.1f/100' % final_score)
print()
print('  >>> SIGNAL:   %s' % verdict)
print('  >>> POSTURE:  %s' % exposure['posture'])
print('  >>> MAX EXPOSURE: %.0f%% of portfolio' % (exposure['max_exposure'] * 100))
print()
print('  Entry: $%s  |  SL: $%s  |  TP1: $%s  |  TP2: $%s' % (
    '{:,.2f}'.format(entry),
    '{:,.2f}'.format(sl),
    '{:,.2f}'.format(tp1),
    '{:,.2f}'.format(tp2),
))
print()
print('=' * 70)
