"""Portfolio Intelligence — extends basic position tracking into real portfolio-risk analysis.

Implements:
- Correlation calculation across held positions
- Beta (vs BTC and total market)
- Concentration metrics (per-asset, per-sector)
- BTC/Stablecoin exposure tracking
- Effective market exposure (netting correlated positions)
- Portfolio-level drawdown tracking
- Value at Risk (VaR)
- Maximum open risk across concurrent positions
"""
import logging
import math
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PortfolioRiskState:
    """Comprehensive portfolio risk state."""
    total_exposure_usd: float
    effective_exposure_usd: float  # Netting correlated positions
    net_exposure_pct: float
    btc_exposure_pct: float
    stablecoin_exposure_pct: float
    concentration: Dict[str, float]  # Per-asset concentration
    hhi: float  # Herfindahl-Hirschman Index (concentration measure)
    max_concentration_asset: str
    max_concentration_pct: float
    correlation_matrix: Dict[str, Dict[str, float]]
    beta_btc: float
    beta_market: float
    var_95: float  # Value at Risk (95% confidence)
    var_99: float  # Value at Risk (99% confidence)
    cvar_95: float  # Conditional VaR (expected shortfall)
    max_drawdown: float
    current_drawdown: float
    total_risk_usd: float
    risk_per_position: Dict[str, float]
    sharpe_ratio: float
    sortino_ratio: float
    portfolio_volatility: float


class PortfolioIntelligence:
    """
    Portfolio intelligence service — extends basic position tracking
    with risk analytics for the Risk Engine.
    """

    def __init__(self, risk_free_rate: float = 0.02):
        """
        Args:
            risk_free_rate: Annual risk-free rate (default 2%)
        """
        self.risk_free_rate = risk_free_rate

    def calculate_correlation(
        self,
        returns: Dict[str, List[float]],
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate correlation matrix between assets.

        Args:
            returns: Dict of {symbol: [period_returns]}

        Returns:
            Correlation matrix
        """
        symbols = list(returns.keys())
        n = len(symbols)
        matrix = {s: {s2: 0.0 for s2 in symbols} for s in symbols}

        for i, s1 in enumerate(symbols):
            for j, s2 in enumerate(symbols):
                if i == j:
                    matrix[s1][s2] = 1.0
                else:
                    corr = self._pearson_correlation(returns[s1], returns[s2])
                    matrix[s1][s2] = corr
                    matrix[s2][s1] = corr

        return matrix

    def calculate_beta(
        self,
        asset_returns: List[float],
        benchmark_returns: List[float],
    ) -> float:
        """
        Calculate beta vs benchmark (e.g., BTC or total market).

        Beta > 1: asset is more volatile than benchmark
        Beta < 1: asset is less volatile than benchmark
        Beta = 1: asset moves with benchmark
        """
        if len(asset_returns) < 2 or len(benchmark_returns) < 2:
            return 1.0

        min_len = min(len(asset_returns), len(benchmark_returns))
        asset = asset_returns[-min_len:]
        bench = benchmark_returns[-min_len:]

        avg_asset = sum(asset) / len(asset)
        avg_bench = sum(bench) / len(bench)

        cov = sum((a - avg_asset) * (b - avg_bench) for a, b in zip(asset, bench)) / len(asset)
        var_bench = sum((b - avg_bench) ** 2 for b in bench) / len(bench)

        if var_bench == 0:
            return 1.0

        return cov / var_bench

    def calculate_concentration(
        self,
        positions: List[Dict],
    ) -> Tuple[Dict[str, float], float, str, float]:
        """
        Calculate concentration metrics.

        Args:
            positions: List of position dicts with 'symbol' and 'current_value_usd'

        Returns:
            Tuple of (concentration_dict, hhi, max_asset, max_pct)
        """
        total = sum(float(p.get('current_value_usd', 0)) for p in positions)
        if total <= 0:
            return {}, 0.0, '', 0.0

        concentration = {}
        hhi = 0.0
        max_asset = ''
        max_pct = 0.0

        for pos in positions:
            symbol = pos.get('symbol', '')
            value = float(pos.get('current_value_usd', 0))
            pct = (value / total * 100) if total > 0 else 0
            concentration[symbol] = pct
            hhi += (pct / 100) ** 2  # HHI uses decimal fractions

            if pct > max_pct:
                max_pct = pct
                max_asset = symbol

        return concentration, hhi, max_asset, max_pct

    def calculate_effective_exposure(
        self,
        positions: List[Dict],
        correlation_matrix: Dict[str, Dict[str, float]],
    ) -> float:
        """
        Calculate effective market exposure, netting correlated positions.

        Naive exposure = sum of all position values
        Effective exposure accounts for correlation:
        - Perfectly correlated positions: effective = naive (no diversification)
        - Uncorrelated positions: effective = naive / sqrt(n) (diversification benefit)
        - Negatively correlated: effective < naive (hedging benefit)
        """
        if not positions:
            return 0.0

        total_value = sum(float(p.get('current_value_usd', 0)) for p in positions)
        if total_value <= 0:
            return 0.0

        # Calculate portfolio variance using correlation matrix
        n = len(positions)
        weights = []
        for pos in positions:
            value = float(pos.get('current_value_usd', 0))
            weights.append(value / total_value if total_value > 0 else 0)

        # Portfolio variance = sum(wi * wj * corr(i,j) * vol_i * vol_j)
        # Simplified: assume unit volatility for each asset
        portfolio_var = 0.0
        for i in range(n):
            for j in range(n):
                symbol_i = positions[i].get('symbol', '')
                symbol_j = positions[j].get('symbol', '')
                corr = correlation_matrix.get(symbol_i, {}).get(symbol_j, 0.5)
                portfolio_var += weights[i] * weights[j] * corr

        # Effective exposure = naive exposure * sqrt(portfolio_var)
        effective_multiplier = math.sqrt(max(0, portfolio_var))
        effective_exposure = total_value * effective_multiplier

        return effective_exposure

    def calculate_var(
        self,
        returns: List[float],
        confidence: float = 0.95,
    ) -> float:
        """
        Calculate Value at Risk using historical simulation.

        Args:
            returns: Historical period returns
            confidence: Confidence level (0.95 or 0.99)

        Returns:
            VaR as a percentage (positive = loss)
        """
        if not returns or len(returns) < 10:
            return 0.0

        sorted_returns = sorted(returns)
        index = int((1 - confidence) * len(sorted_returns))
        index = max(0, min(index, len(sorted_returns) - 1))

        return abs(sorted_returns[index])

    def calculate_cvar(
        self,
        returns: List[float],
        confidence: float = 0.95,
    ) -> float:
        """
        Calculate Conditional VaR (Expected Shortfall).
        Average loss in the worst (1-confidence)% of cases.
        """
        if not returns or len(returns) < 10:
            return 0.0

        sorted_returns = sorted(returns)
        cutoff = int((1 - confidence) * len(sorted_returns))
        cutoff = max(1, cutoff)

        worst_returns = sorted_returns[:cutoff]
        return abs(sum(worst_returns) / len(worst_returns))

    def calculate_drawdown(
        self,
        equity_curve: List[float],
    ) -> Tuple[float, float]:
        """
        Calculate maximum drawdown and current drawdown.

        Returns:
            Tuple of (max_drawdown_pct, current_drawdown_pct)
        """
        if not equity_curve or len(equity_curve) < 2:
            return 0.0, 0.0

        peak = equity_curve[0]
        max_dd = 0.0

        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100 if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd

        current_dd = (peak - equity_curve[-1]) / peak * 100 if peak > 0 else 0

        return max_dd, current_dd

    def calculate_sharpe_ratio(
        self,
        returns: List[float],
        period_annualization: float = 365,
    ) -> float:
        """Calculate annualized Sharpe ratio."""
        if not returns or len(returns) < 2:
            return 0.0

        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = math.sqrt(variance) if variance > 0 else 0

        if std_dev == 0:
            return 0.0

        daily_rf = self.risk_free_rate / period_annualization
        return (avg_return - daily_rf) / std_dev * math.sqrt(period_annualization)

    def calculate_sortino_ratio(
        self,
        returns: List[float],
        period_annualization: float = 365,
    ) -> float:
        """Calculate annualized Sortino ratio (only penalizes downside)."""
        if not returns or len(returns) < 2:
            return 0.0

        avg_return = sum(returns) / len(returns)
        downside_returns = [r for r in returns if r < 0]

        if not downside_returns:
            return 10.0  # No downside

        downside_var = sum(r ** 2 for r in downside_returns) / len(downside_returns)
        downside_std = math.sqrt(downside_var)

        if downside_std == 0:
            return 10.0

        daily_rf = self.risk_free_rate / period_annualization
        return (avg_return - daily_rf) / downside_std * math.sqrt(period_annualization)

    def get_portfolio_risk_state(
        self,
        positions: List[Dict],
        returns_data: Dict[str, List[float]] = None,
        benchmark_returns: List[float] = None,
        equity_curve: List[float] = None,
        btc_returns: List[float] = None,
    ) -> PortfolioRiskState:
        """
        Get comprehensive portfolio risk state.

        Args:
            positions: Current positions with symbol, current_value_usd, side
            returns_data: Historical returns per asset
            benchmark_returns: Market benchmark returns
            equity_curve: Portfolio equity curve
            btc_returns: BTC returns (for beta calculation)
        """
        returns_data = returns_data or {}
        benchmark_returns = benchmark_returns or []
        equity_curve = equity_curve or []
        btc_returns = btc_returns or []

        total_value = sum(float(p.get('current_value_usd', 0)) for p in positions)

        # Correlation
        correlation = self.calculate_correlation(returns_data) if returns_data else {}

        # Concentration
        concentration, hhi, max_asset, max_pct = self.calculate_concentration(positions)

        # Effective exposure
        effective = self.calculate_effective_exposure(positions, correlation)

        # BTC / Stablecoin exposure
        btc_symbols = {'BTC', 'BTCUSDT', 'WBTC', 'BTCUSDT.P'}
        stable_symbols = {'USDT', 'USDC', 'BUSD', 'DAI', 'TUSD', 'USDP'}
        btc_exposure = 0.0
        stable_exposure = 0.0
        for pos in positions:
            symbol = pos.get('symbol', '').upper()
            value = float(pos.get('current_value_usd', 0))
            base = symbol.split('/')[0] if '/' in symbol else symbol.replace('USDT', '').replace('USD', '')
            if base in btc_symbols or 'BTC' in symbol:
                btc_exposure += value
            elif base in stable_symbols or symbol in stable_symbols:
                stable_exposure += value

        btc_pct = (btc_exposure / total_value * 100) if total_value > 0 else 0
        stable_pct = (stable_exposure / total_value * 100) if total_value > 0 else 0

        # Beta
        avg_asset_returns = []
        for symbol, rets in returns_data.items():
            if rets:
                avg_asset_returns.extend(rets)
        beta_btc = self.calculate_beta(avg_asset_returns, btc_returns) if btc_returns else 1.0
        beta_market = self.calculate_beta(avg_asset_returns, benchmark_returns) if benchmark_returns else 1.0

        # VaR
        portfolio_returns = []
        if returns_data:
            # Equal-weight portfolio returns for VaR estimation
            all_returns = list(returns_data.values())
            if all_returns:
                min_len = min(len(r) for r in all_returns if r)
                if min_len > 0:
                    for i in range(min_len):
                        avg_ret = sum(r[i] for r in all_returns if len(r) > i) / len(all_returns)
                        portfolio_returns.append(avg_ret)

        var_95 = self.calculate_var(portfolio_returns, 0.95) * total_value
        var_99 = self.calculate_var(portfolio_returns, 0.99) * total_value
        cvar_95 = self.calculate_cvar(portfolio_returns, 0.95) * total_value

        # Drawdown
        max_dd, current_dd = self.calculate_drawdown(equity_curve) if equity_curve else (0.0, 0.0)

        # Risk per position
        risk_per_pos = {}
        for pos in positions:
            symbol = pos.get('symbol', '')
            risk = float(pos.get('risk_amount', 0))
            risk_per_pos[symbol] = risk

        total_risk = sum(risk_per_pos.values())

        # Ratios
        sharpe = self.calculate_sharpe_ratio(portfolio_returns)
        sortino = self.calculate_sortino_ratio(portfolio_returns)

        # Volatility
        if portfolio_returns and len(portfolio_returns) > 1:
            avg_ret = sum(portfolio_returns) / len(portfolio_returns)
            var = sum((r - avg_ret) ** 2 for r in portfolio_returns) / len(portfolio_returns)
            volatility = math.sqrt(var) * math.sqrt(365)  # Annualized
        else:
            volatility = 0.0

        return PortfolioRiskState(
            total_exposure_usd=total_value,
            effective_exposure_usd=effective,
            net_exposure_pct=(effective / total_value * 100) if total_value > 0 else 0,
            btc_exposure_pct=btc_pct,
            stablecoin_exposure_pct=stable_pct,
            concentration=concentration,
            hhi=hhi,
            max_concentration_asset=max_asset,
            max_concentration_pct=max_pct,
            correlation_matrix=correlation,
            beta_btc=beta_btc,
            beta_market=beta_market,
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            max_drawdown=max_dd,
            current_drawdown=current_dd,
            total_risk_usd=total_risk,
            risk_per_position=risk_per_pos,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            portfolio_volatility=volatility,
        )

    def _pearson_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        n = min(len(x), len(y))
        if n < 2:
            return 0.0

        x = x[-n:]
        y = y[-n:]

        avg_x = sum(x) / n
        avg_y = sum(y) / n

        cov = sum((xi - avg_x) * (yi - avg_y) for xi, yi in zip(x, y)) / n
        std_x = math.sqrt(sum((xi - avg_x) ** 2 for xi in x) / n)
        std_y = math.sqrt(sum((yi - avg_y) ** 2 for yi in y) / n)

        if std_x == 0 or std_y == 0:
            return 0.0

        return cov / (std_x * std_y)
