"""Portfolio views."""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Portfolio, PortfolioAllocation, RebalanceHistory, TaxLot, TaxReport
from .serializers import (PortfolioSerializer, PortfolioAllocationSerializer,
                          RebalanceHistorySerializer, TaxLotSerializer, TaxReportSerializer)
from .services.rebalancer import PortfolioRebalancer
from .services.tax_optimizer import TaxOptimizer


class PortfolioViewSet(viewsets.ModelViewSet):
    """API endpoint for portfolio management."""
    serializer_class = PortfolioSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def rebalance(self, request, pk=None):
        """Trigger portfolio rebalancing."""
        portfolio = self.get_object()
        rebalancer = PortfolioRebalancer()
        
        # Get current holdings
        allocations = PortfolioAllocation.objects.filter(portfolio=portfolio)
        current_holdings = {
            a.symbol: a.current_value_usd for a in allocations
        }
        
        # Get target allocation
        target_allocation = {
            a.symbol: a.target_percent for a in allocations
        }
        
        # Calculate trades
        trades = rebalancer.calculate_rebalance_trades(
            current_holdings,
            target_allocation,
            portfolio.total_value_usd
        )
        
        # Create rebalance history
        history = RebalanceHistory.objects.create(
            portfolio=portfolio,
            status='pending',
            trades_executed=trades,
            total_trades=len(trades),
            portfolio_value_before=portfolio.total_value_usd,
            triggered_by='manual',
        )
        
        return Response({
            'rebalance_id': str(history.id),
            'trades': trades,
            'total_trades': len(trades),
        })
    
    @action(detail=True, methods=['get'])
    def check_rebalance(self, request, pk=None):
        """Check if rebalancing is needed."""
        portfolio = self.get_object()
        rebalancer = PortfolioRebalancer()
        
        allocations = PortfolioAllocation.objects.filter(portfolio=portfolio)
        current = {a.symbol: a.current_percent for a in allocations}
        target = {a.symbol: a.target_percent for a in allocations}
        
        needs_rebalance, drifted = rebalancer.check_rebalance_needed(
            current, target, portfolio.rebalance_threshold_percent
        )
        
        return Response({
            'needs_rebalance': needs_rebalance,
            'drifted_assets': drifted,
        })
    
    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        """Get portfolio performance metrics."""
        portfolio = self.get_object()
        
        return Response({
            'total_value': float(portfolio.total_value_usd),
            'total_invested': float(portfolio.total_invested_usd),
            'total_pnl': float(portfolio.total_pnl_usd),
            'pnl_percent': float(portfolio.total_pnl_percent),
            'sharpe_ratio': float(portfolio.sharpe_ratio),
            'max_drawdown': float(portfolio.max_drawdown),
            'volatility': float(portfolio.volatility),
        })


class PortfolioAllocationViewSet(viewsets.ModelViewSet):
    """API endpoint for portfolio allocations."""
    serializer_class = PortfolioAllocationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        portfolio_id = self.request.query_params.get('portfolio')
        if portfolio_id:
            return PortfolioAllocation.objects.filter(portfolio_id=portfolio_id)
        return PortfolioAllocation.objects.none()


class RebalanceHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for rebalance history."""
    serializer_class = RebalanceHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        portfolio_id = self.request.query_params.get('portfolio')
        if portfolio_id:
            return RebalanceHistory.objects.filter(portfolio_id=portfolio_id)
        return RebalanceHistory.objects.none()


class TaxLotViewSet(viewsets.ModelViewSet):
    """API endpoint for tax lot management."""
    serializer_class = TaxLotSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        portfolio_id = self.request.query_params.get('portfolio')
        if portfolio_id:
            return TaxLot.objects.filter(portfolio_id=portfolio_id)
        return TaxLot.objects.none()


class TaxReportViewSet(viewsets.ModelViewSet):
    """API endpoint for tax reports."""
    serializer_class = TaxReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        portfolio_id = self.request.query_params.get('portfolio')
        if portfolio_id:
            return TaxReport.objects.filter(portfolio_id=portfolio_id)
        return TaxReport.objects.none()
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate a tax report for a portfolio."""
        portfolio_id = request.data.get('portfolio')
        tax_year = request.data.get('tax_year', 2024)
        
        if not portfolio_id:
            return Response(
                {'error': 'portfolio is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get tax lots for the year
        tax_lots = TaxLot.objects.filter(
            portfolio_id=portfolio_id,
            disposition_date__year=tax_year
        )
        
        optimizer = TaxOptimizer()
        lots_data = [
            {
                'disposition_date': str(lot.disposition_date),
                'proceeds': float(lot.proceeds_usd or 0),
                'cost_basis': float(lot.cost_basis_usd),
                'gain_loss': float(lot.gain_loss_usd or 0),
                'is_long_term': lot.is_long_term,
            }
            for lot in tax_lots
        ]
        
        report = optimizer.generate_tax_report(lots_data, tax_year)
        
        # Save report
        tax_report = TaxReport.objects.create(
            portfolio_id=portfolio_id,
            tax_year=tax_year,
            total_proceeds=report['total_proceeds'],
            total_cost_basis=report['total_cost_basis'],
            total_gain_loss=report['total_gain_loss'],
            short_term_proceeds=report['short_term_proceeds'],
            short_term_gain_loss=report['short_term_gain_loss'],
            long_term_proceeds=report['long_term_proceeds'],
            long_term_gain_loss=report['long_term_gain_loss'],
            transactions=lots_data,
        )
        
        return Response(TaxReportSerializer(tax_report).data)
