"""Portfolio Intelligence tests — correlation, VaR, beta, concentration, effective exposure."""
import math
from decimal import Decimal
from django.test import TestCase
from .services.portfolio_intelligence import PortfolioIntelligence


class CorrelationTest(TestCase):
    """Tests for correlation calculation."""

    def setUp(self):
        self.pi = PortfolioIntelligence()

    def test_perfect_correlation(self):
        """Identical returns should have correlation of 1.0."""
        returns = {'A': [0.01, 0.02, 0.03, 0.04], 'B': [0.01, 0.02, 0.03, 0.04]}
        matrix = self.pi.calculate_correlation(returns)
        self.assertAlmostEqual(matrix['A']['B'], 1.0, places=4)

    def test_inverse_correlation(self):
        """Opposite returns should have correlation near -1.0."""
        returns = {'A': [0.01, 0.02, 0.03, 0.04], 'B': [-0.01, -0.02, -0.03, -0.04]}
        matrix = self.pi.calculate_correlation(returns)
        self.assertAlmostEqual(matrix['A']['B'], -1.0, places=4)

    def test_zero_correlation(self):
        """Uncorrelated returns should have correlation near 0."""
        returns = {'A': [0.01, -0.01, 0.01, -0.01], 'B': [0.02, 0.02, -0.02, -0.02]}
        matrix = self.pi.calculate_correlation(returns)
        self.assertAlmostEqual(matrix['A']['B'], 0.0, places=1)

    def test_self_correlation(self):
        """Asset should correlate perfectly with itself."""
        returns = {'A': [0.01, 0.02, 0.03]}
        matrix = self.pi.calculate_correlation(returns)
        self.assertAlmostEqual(matrix['A']['A'], 1.0, places=4)

    def test_symmetric_matrix(self):
        """Correlation matrix should be symmetric."""
        returns = {'A': [0.01, 0.02, 0.03], 'B': [0.02, 0.03, 0.04], 'C': [0.03, 0.04, 0.05]}
        matrix = self.pi.calculate_correlation(returns)
        for s1 in returns:
            for s2 in returns:
                self.assertAlmostEqual(matrix[s1][s2], matrix[s2][s1], places=10)

    def test_empty_returns(self):
        """Empty returns should produce zero correlation."""
        matrix = self.pi.calculate_correlation({})
        self.assertEqual(matrix, {})


class BetaTest(TestCase):
    """Tests for beta calculation."""

    def setUp(self):
        self.pi = PortfolioIntelligence()

    def test_beta_with_benchmark(self):
        """Asset moving with benchmark should have beta near 1."""
        asset = [0.01, 0.02, 0.015, 0.025, 0.01]
        bench = [0.01, 0.02, 0.015, 0.025, 0.01]
        beta = self.pi.calculate_beta(asset, bench)
        self.assertAlmostEqual(beta, 1.0, places=4)

    def test_beta_higher_volatility(self):
        """Asset with higher swings should have beta > 1."""
        asset = [0.02, 0.04, 0.03, 0.05, 0.02]
        bench = [0.01, 0.02, 0.015, 0.025, 0.01]
        beta = self.pi.calculate_beta(asset, bench)
        self.assertGreater(beta, 1.0)

    def test_beta_lower_volatility(self):
        """Asset with lower swings should have beta < 1."""
        asset = [0.005, 0.01, 0.007, 0.012, 0.005]
        bench = [0.01, 0.02, 0.015, 0.025, 0.01]
        beta = self.pi.calculate_beta(asset, bench)
        self.assertLess(beta, 1.0)

    def test_beta_empty_data(self):
        """Empty data should return default beta of 1."""
        beta = self.pi.calculate_beta([], [])
        self.assertEqual(beta, 1.0)


class ConcentrationTest(TestCase):
    """Tests for concentration metrics."""

    def setUp(self):
        self.pi = PortfolioIntelligence()

    def test_equal_weight(self):
        """Equal positions should have equal concentration."""
        positions = [
            {'symbol': 'BTC', 'current_value_usd': 5000},
            {'symbol': 'ETH', 'current_value_usd': 5000},
        ]
        conc, hhi, max_asset, max_pct = self.pi.calculate_concentration(positions)
        self.assertAlmostEqual(conc['BTC'], 50.0, places=1)
        self.assertAlmostEqual(conc['ETH'], 50.0, places=1)
        self.assertEqual(max_pct, 50.0)

    def test_concentrated_portfolio(self):
        """One large position should show high concentration."""
        positions = [
            {'symbol': 'BTC', 'current_value_usd': 9000},
            {'symbol': 'ETH', 'current_value_usd': 1000},
        ]
        conc, hhi, max_asset, max_pct = self.pi.calculate_concentration(positions)
        self.assertAlmostEqual(conc['BTC'], 90.0, places=1)
        self.assertEqual(max_asset, 'BTC')
        self.assertAlmostEqual(max_pct, 90.0, places=1)

    def test_hhi_range(self):
        """HHI should be between 0 and 1."""
        positions = [
            {'symbol': 'BTC', 'current_value_usd': 3000},
            {'symbol': 'ETH', 'current_value_usd': 3000},
            {'symbol': 'SOL', 'current_value_usd': 4000},
        ]
        _, hhi, _, _ = self.pi.calculate_concentration(positions)
        self.assertGreaterEqual(hhi, 0)
        self.assertLessEqual(hhi, 1)

    def test_empty_positions(self):
        """Empty positions should return zero concentration."""
        conc, hhi, max_asset, max_pct = self.pi.calculate_concentration([])
        self.assertEqual(conc, {})
        self.assertEqual(hhi, 0.0)


class EffectiveExposureTest(TestCase):
    """Tests for effective exposure calculation."""

    def setUp(self):
        self.pi = PortfolioIntelligence()

    def test_single_position(self):
        """Single position should have effective = naive exposure."""
        positions = [{'symbol': 'BTC', 'current_value_usd': 10000}]
        corr = {'BTC': {'BTC': 1.0}}
        effective = self.pi.calculate_effective_exposure(positions, corr)
        self.assertAlmostEqual(effective, 10000.0, places=0)

    def test_perfectly_correlated(self):
        """Perfectly correlated positions should have effective = naive."""
        positions = [
            {'symbol': 'BTC', 'current_value_usd': 5000},
            {'symbol': 'WBTC', 'current_value_usd': 5000},
        ]
        corr = {'BTC': {'BTC': 1.0, 'WBTC': 1.0}, 'WBTC': {'BTC': 1.0, 'WBTC': 1.0}}
        effective = self.pi.calculate_effective_exposure(positions, corr)
        self.assertAlmostEqual(effective, 10000.0, places=0)

    def test_uncorrelated_positions(self):
        """Uncorrelated positions should have effective < naive (diversification)."""
        positions = [
            {'symbol': 'BTC', 'current_value_usd': 5000},
            {'symbol': 'SOL', 'current_value_usd': 5000},
        ]
        corr = {'BTC': {'BTC': 1.0, 'SOL': 0.0}, 'SOL': {'BTC': 0.0, 'SOL': 1.0}}
        effective = self.pi.calculate_effective_exposure(positions, corr)
        self.assertLess(effective, 10000.0)
        self.assertGreater(effective, 0)

    def test_negatively_correlated(self):
        """Negatively correlated positions should have effective << naive (hedging)."""
        positions = [
            {'symbol': 'BTC', 'current_value_usd': 5000},
            {'symbol': 'SHORT_BTC', 'current_value_usd': 5000},
        ]
        corr = {'BTC': {'BTC': 1.0, 'SHORT_BTC': -1.0}, 'SHORT_BTC': {'BTC': -1.0, 'SHORT_BTC': 1.0}}
        effective = self.pi.calculate_effective_exposure(positions, corr)
        self.assertLess(effective, 10000.0)


class VaRTest(TestCase):
    """Tests for Value at Risk calculation."""

    def setUp(self):
        self.pi = PortfolioIntelligence()

    def test_var_positive(self):
        """VaR should be positive (representing potential loss)."""
        returns = [-0.02, -0.01, 0.01, 0.02, -0.03, 0.01, -0.01, 0.02, -0.02, 0.01, -0.04, 0.01]
        var = self.pi.calculate_var(returns, 0.95)
        self.assertGreater(var, 0)

    def test_var_99_higher_than_95(self):
        """99% VaR should be higher than 95% VaR (worse loss)."""
        returns = [-0.05, -0.04, -0.03, -0.02, -0.01, 0.01, 0.02, 0.03, 0.04, 0.05]
        var_95 = self.pi.calculate_var(returns, 0.95)
        var_99 = self.pi.calculate_var(returns, 0.99)
        self.assertGreaterEqual(var_99, var_95)

    def test_cvar_higher_than_var(self):
        """CVaR should be higher than VaR (expected shortfall)."""
        returns = [-0.05, -0.04, -0.03, -0.02, -0.01, 0.01, 0.02, 0.03, 0.04, 0.05, -0.06, 0.02]
        var = self.pi.calculate_var(returns, 0.95)
        cvar = self.pi.calculate_cvar(returns, 0.95)
        self.assertGreaterEqual(cvar, var)

    def test_var_empty_returns(self):
        """Empty returns should return 0."""
        var = self.pi.calculate_var([], 0.95)
        self.assertEqual(var, 0.0)


class DrawdownTest(TestCase):
    """Tests for drawdown calculation."""

    def setUp(self):
        self.pi = PortfolioIntelligence()

    def test_max_drawdown(self):
        """Should correctly calculate maximum drawdown."""
        equity = [10000, 11000, 9000, 9500, 8500, 10000]
        max_dd, current_dd = self.pi.calculate_drawdown(equity)
        # Peak was 11000, trough was 8500 -> dd = 22.7%
        self.assertAlmostEqual(max_dd, 22.73, places=1)

    def test_no_drawdown(self):
        """Monotonically increasing equity should have 0 drawdown."""
        equity = [10000, 11000, 12000, 13000]
        max_dd, current_dd = self.pi.calculate_drawdown(equity)
        self.assertEqual(max_dd, 0.0)

    def test_current_drawdown(self):
        """Current drawdown should be from peak to current."""
        equity = [10000, 12000, 11000]
        max_dd, current_dd = self.pi.calculate_drawdown(equity)
        # Peak 12000, current 11000 -> dd = 8.33%
        self.assertAlmostEqual(current_dd, 8.33, places=1)


class SharpeRatioTest(TestCase):
    """Tests for Sharpe and Sortino ratios."""

    def setUp(self):
        self.pi = PortfolioIntelligence()

    def test_sharpe_positive_returns(self):
        """Consistently positive returns should give positive Sharpe."""
        returns = [0.01, 0.02, 0.01, 0.02, 0.01, 0.02, 0.01, 0.02]
        sharpe = self.pi.calculate_sharpe_ratio(returns)
        self.assertGreater(sharpe, 0)

    def test_sortino_positive_returns(self):
        """No negative returns should give high Sortino."""
        returns = [0.01, 0.02, 0.01, 0.02, 0.01, 0.02]
        sortino = self.pi.calculate_sortino_ratio(returns)
        self.assertGreater(sortino, 0)

    def test_sharpe_empty(self):
        """Empty returns should give 0 Sharpe."""
        sharpe = self.pi.calculate_sharpe_ratio([])
        self.assertEqual(sharpe, 0.0)


class PortfolioRiskStateTest(TestCase):
    """Tests for comprehensive portfolio risk state."""

    def setUp(self):
        self.pi = PortfolioIntelligence()
        self.positions = [
            {'symbol': 'BTC', 'current_value_usd': 6000, 'risk_amount': 100},
            {'symbol': 'ETH', 'current_value_usd': 3000, 'risk_amount': 80},
            {'symbol': 'SOL', 'current_value_usd': 1000, 'risk_amount': 50},
        ]
        self.returns = {
            'BTC': [0.01, 0.02, -0.01, 0.03, 0.01, -0.02, 0.02, 0.01, -0.01, 0.02],
            'ETH': [0.02, 0.03, -0.02, 0.04, 0.02, -0.03, 0.03, 0.02, -0.02, 0.03],
            'SOL': [0.03, 0.04, -0.03, 0.05, 0.03, -0.04, 0.04, 0.03, -0.03, 0.04],
        }

    def test_total_exposure(self):
        """Total exposure should equal sum of positions."""
        state = self.pi.get_portfolio_risk_state(self.positions, self.returns)
        self.assertAlmostEqual(state.total_exposure_usd, 10000.0, places=0)

    def test_btc_exposure(self):
        """BTC exposure should be 60%."""
        state = self.pi.get_portfolio_risk_state(self.positions, self.returns)
        self.assertAlmostEqual(state.btc_exposure_pct, 60.0, places=1)

    def test_concentration(self):
        """Max concentration should be BTC at 60%."""
        state = self.pi.get_portfolio_risk_state(self.positions, self.returns)
        self.assertEqual(state.max_concentration_asset, 'BTC')
        self.assertAlmostEqual(state.max_concentration_pct, 60.0, places=1)

    def test_correlation_matrix(self):
        """Should have correlation matrix for all assets."""
        state = self.pi.get_portfolio_risk_state(self.positions, self.returns)
        self.assertIn('BTC', state.correlation_matrix)
        self.assertIn('ETH', state.correlation_matrix)
        self.assertIn('SOL', state.correlation_matrix)

    def test_var_positive(self):
        """VaR should be positive."""
        state = self.pi.get_portfolio_risk_state(self.positions, self.returns)
        self.assertGreater(state.var_95, 0)

    def test_risk_per_position(self):
        """Should track risk per position."""
        state = self.pi.get_portfolio_risk_state(self.positions, self.returns)
        self.assertIn('BTC', state.risk_per_position)
        self.assertIn('ETH', state.risk_per_position)
        self.assertEqual(state.risk_per_position['BTC'], 100)

    def test_empty_positions(self):
        """Empty positions should return zero state."""
        state = self.pi.get_portfolio_risk_state([], {})
        self.assertEqual(state.total_exposure_usd, 0)
        self.assertEqual(state.var_95, 0)

    def test_beta_with_btc(self):
        """Should calculate beta vs BTC."""
        btc_returns = [0.01, 0.02, -0.01, 0.03, 0.01, -0.02, 0.02, 0.01, -0.01, 0.02]
        state = self.pi.get_portfolio_risk_state(
            self.positions, self.returns, btc_returns=btc_returns
        )
        self.assertIsInstance(state.beta_btc, float)
        self.assertGreater(state.beta_btc, 0)
