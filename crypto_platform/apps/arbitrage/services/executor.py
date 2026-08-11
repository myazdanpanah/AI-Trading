"""Arbitrage execution service - Automatically execute arbitrage opportunities."""
import logging
import asyncio
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class ArbitrageExecutor:
    """Handles automatic execution of arbitrage opportunities."""
    
    def __init__(self):
        self.min_profit_usd = Decimal('50')  # Minimum profit to execute
        self.max_position_usd = Decimal('10000')  # Maximum position size
        self.slippage_tolerance = Decimal('0.001')  # 0.1% slippage tolerance
        
    async def execute_arbitrage(
        self,
        opportunity: Dict,
        exchange_clients: Dict,
    ) -> Dict:
        """
        Execute an arbitrage opportunity.
        
        Args:
            opportunity: Arbitrage opportunity data
            exchange_clients: {exchange_name: exchange_client}
            
        Returns:
            Execution result
        """
        result = {
            'status': 'pending',
            'opportunity_id': opportunity.get('id'),
            'trades': [],
            'total_profit_usd': Decimal('0'),
            'fees_paid': Decimal('0'),
            'execution_time_ms': 0,
            'error': None,
        }
        
        start_time = datetime.now()
        
        try:
            # Validate opportunity
            if not self._validate_opportunity(opportunity):
                result['status'] = 'rejected'
                result['error'] = 'Opportunity validation failed'
                return result
            
            # Calculate position size
            position_size = self._calculate_position_size(opportunity)
            
            # Execute buy order
            buy_client = exchange_clients.get(opportunity['buy_exchange'])
            if not buy_client:
                result['status'] = 'failed'
                result['error'] = f"No client for {opportunity['buy_exchange']}"
                return result
            
            buy_result = await self._execute_buy_order(
                buy_client,
                opportunity['symbol'],
                position_size,
                opportunity['buy_price'],
            )
            
            if not buy_result['success']:
                result['status'] = 'failed'
                result['error'] = f"Buy order failed: {buy_result.get('error')}"
                return result
            
            result['trades'].append({
                'exchange': opportunity['buy_exchange'],
                'side': 'buy',
                'order_id': buy_result.get('order_id'),
                'price': float(opportunity['buy_price']),
                'quantity': float(position_size),
            })
            
            # Execute sell order
            sell_client = exchange_clients.get(opportunity['sell_exchange'])
            if not sell_client:
                result['status'] = 'partial'
                result['error'] = f"No client for {opportunity['sell_exchange']}, position held"
                return result
            
            sell_result = await self._execute_sell_order(
                sell_client,
                opportunity['symbol'],
                position_size,
                opportunity['sell_price'],
            )
            
            if not sell_result['success']:
                result['status'] = 'partial'
                result['error'] = f"Sell order failed: {sell_result.get('error')}, position held"
                return result
            
            result['trades'].append({
                'exchange': opportunity['sell_exchange'],
                'side': 'sell',
                'order_id': sell_result.get('order_id'),
                'price': float(opportunity['sell_price']),
                'quantity': float(position_size),
            })
            
            # Calculate profit
            buy_cost = position_size * opportunity['buy_price']
            sell_proceeds = position_size * opportunity['sell_price']
            gross_profit = sell_proceeds - buy_cost
            
            # Estimate fees
            buy_fee = buy_cost * Decimal('0.001')  # 0.1%
            sell_fee = sell_proceeds * Decimal('0.001')
            total_fees = buy_fee + sell_fee
            
            net_profit = gross_profit - total_fees
            
            result['status'] = 'completed'
            result['total_profit_usd'] = net_profit
            result['fees_paid'] = total_fees
            
            logger.info(f"Arbitrage executed: {opportunity['symbol']} - Profit: ${net_profit}")
            
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            logger.error(f"Arbitrage execution failed: {e}")
        
        finally:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            result['execution_time_ms'] = int(execution_time)
        
        return result
    
    def _validate_opportunity(self, opportunity: Dict) -> bool:
        """Validate an arbitrage opportunity before execution."""
        # Check minimum profit
        net_profit = Decimal(str(opportunity.get('net_profit_percent', 0)))
        if net_profit < Decimal('0.5'):  # Minimum 0.5% profit
            return False
        
        # Check risk score
        risk_score = opportunity.get('risk_score', 100)
        if risk_score > 70:
            return False
        
        # Check volume
        volume = Decimal(str(opportunity.get('volume_available', 0)))
        if volume < self.min_profit_usd * 10:
            return False
        
        return True
    
    def _calculate_position_size(self, opportunity: Dict) -> Decimal:
        """Calculate optimal position size for execution."""
        volume = Decimal(str(opportunity.get('volume_available', 0)))
        spread = Decimal(str(opportunity.get('spread_percent', 0)))
        
        # Conservative sizing
        if spread > 2:
            size = min(volume * Decimal('0.05'), self.max_position_usd)
        elif spread > 1:
            size = min(volume * Decimal('0.02'), self.max_position_usd * Decimal('0.5'))
        else:
            size = min(volume * Decimal('0.01'), self.max_position_usd * Decimal('0.25'))
        
        return max(Decimal('100'), size)  # Minimum $100
    
    async def _execute_buy_order(
        self,
        client,
        symbol: str,
        quantity: Decimal,
        max_price: Decimal,
    ) -> Dict:
        """Execute a buy order on an exchange."""
        try:
            # In production, this would call the actual exchange API
            order = await client.create_order(
                symbol=symbol,
                side='buy',
                amount=float(quantity),
                price=float(max_price),
            )
            
            return {
                'success': True,
                'order_id': order.get('id'),
                'filled_price': order.get('price'),
                'filled_quantity': order.get('amount'),
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }
    
    async def _execute_sell_order(
        self,
        client,
        symbol: str,
        quantity: Decimal,
        min_price: Decimal,
    ) -> Dict:
        """Execute a sell order on an exchange."""
        try:
            # In production, this would call the actual exchange API
            order = await client.create_order(
                symbol=symbol,
                side='sell',
                amount=float(quantity),
                price=float(min_price),
            )
            
            return {
                'success': True,
                'order_id': order.get('id'),
                'filled_price': order.get('price'),
                'filled_quantity': order.get('amount'),
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }


class ArbitrageMonitor:
    """Continuously monitor and execute arbitrage opportunities."""
    
    def __init__(self, executor: ArbitrageExecutor):
        self.executor = executor
        self.is_running = False
        self.opportunities = []
        self.execution_history = []
        
    async def start_monitoring(
        self,
        detector,
        exchange_clients: Dict,
        check_interval: int = 30,
    ):
        """Start monitoring for arbitrage opportunities."""
        self.is_running = True
        logger.info("Arbitrage monitoring started")
        
        while self.is_running:
            try:
                # Scan for opportunities
                self.opportunities = detector.find_opportunities(
                    min_spread_percent=Decimal('0.5'),
                    volume_threshold=Decimal('1000'),
                )
                
                # Execute profitable opportunities
                for opp in self.opportunities:
                    if opp.get('net_profit_percent', 0) > 1.0:  # >1% profit
                        result = await self.executor.execute_arbitrage(
                            opp,
                            exchange_clients,
                        )
                        self.execution_history.append(result)
                
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(check_interval)
    
    def stop_monitoring(self):
        """Stop monitoring for arbitrage opportunities."""
        self.is_running = False
        logger.info("Arbitrage monitoring stopped")
    
    def get_status(self) -> Dict:
        """Get monitoring status."""
        return {
            'is_running': self.is_running,
            'opportunities_found': len(self.opportunities),
            'executions': len(self.execution_history),
            'successful_executions': len([
                e for e in self.execution_history
                if e.get('status') == 'completed'
            ]),
            'total_profit': sum(
                e.get('total_profit_usd', 0)
                for e in self.execution_history
            ),
        }
