"""Tax optimization service - Tax-loss harvesting and cost basis tracking."""
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class TaxOptimizer:
    """Handles tax optimization strategies for crypto portfolios."""
    
    # Tax rates (simplified US federal)
    SHORT_TERM_RATE = Decimal('0.22')  # 22% for income bracket
    LONG_TERM_RATE = Decimal('0.15')   # 15% for income bracket
    WASH_SALE_DAYS = 30  # IRS wash sale rule
    
    def calculate_tax_lots(
        self,
        transactions: List[Dict],
        method: str = 'fifo',
    ) -> List[Dict]:
        """
        Calculate tax lots using specified cost basis method.
        
        Args:
            transactions: List of buy/sell transactions
            method: 'fifo', 'lifo', 'hifo' (highest in, first out)
            
        Returns:
            List of tax lots with gain/loss calculations
        """
        # Group by symbol
        symbol_transactions = defaultdict(list)
        for tx in transactions:
            symbol = tx.get('symbol', '')
            symbol_transactions[symbol].append(tx)
        
        tax_lots = []
        
        for symbol, txs in symbol_transactions.items():
            # Sort by date
            txs.sort(key=lambda x: x.get('date', ''))
            
            open_lots = []  # [(date, quantity, cost_basis)]
            
            for tx in txs:
                tx_type = tx.get('type', '').lower()
                date = tx.get('date', '')
                quantity = Decimal(str(tx.get('quantity', 0)))
                price = Decimal(str(tx.get('price', 0)))
                total_cost = quantity * price
                
                if tx_type == 'buy':
                    open_lots.append({
                        'date': date,
                        'quantity': quantity,
                        'cost_basis': total_cost,
                        'cost_per_unit': price,
                    })
                
                elif tx_type == 'sell':
                    remaining = quantity
                    
                    # Sort open lots by method
                    if method == 'fifo':
                        sorted_lots = open_lots.copy()
                    elif method == 'lifo':
                        sorted_lots = open_lots[::-1]
                    elif method == 'hifo':
                        sorted_lots = sorted(open_lots, key=lambda x: x['cost_per_unit'], reverse=True)
                    else:
                        sorted_lots = open_lots.copy()
                    
                    for lot in sorted_lots:
                        if remaining <= 0:
                            break
                        
                        if lot['quantity'] <= 0:
                            continue
                        
                        # Calculate lot quantity to use
                        lot_quantity = min(lot['quantity'], remaining)
                        remaining -= lot_quantity
                        
                        # Calculate gain/loss
                        cost_basis = lot_quantity * lot['cost_per_unit']
                        proceeds = lot_quantity * price
                        gain_loss = proceeds - cost_basis
                        
                        # Calculate holding period
                        lot_date = datetime.strptime(lot['date'], '%Y-%m-%d') if lot['date'] else datetime.now()
                        sell_date = datetime.strptime(date, '%Y-%m-%d') if date else datetime.now()
                        holding_days = (sell_date - lot_date).days
                        is_long_term = holding_days > 365
                        
                        tax_lots.append({
                            'symbol': symbol,
                            'acquisition_date': lot['date'],
                            'disposition_date': date,
                            'quantity': float(lot_quantity),
                            'cost_basis_per_unit': float(lot['cost_per_unit']),
                            'proceeds_per_unit': float(price),
                            'cost_basis': float(cost_basis),
                            'proceeds': float(proceeds),
                            'gain_loss': float(gain_loss),
                            'gain_loss_percent': float((gain_loss / cost_basis * 100) if cost_basis > 0 else 0),
                            'holding_days': holding_days,
                            'is_long_term': is_long_term,
                            'tax_rate': float(self.LONG_TERM_RATE if is_long_term else self.SHORT_TERM_RATE),
                        })
                        
                        # Update lot
                        lot['quantity'] -= lot_quantity
                    
                    # Remove empty lots
                    open_lots = [l for l in open_lots if l['quantity'] > 0]
        
        return tax_lots
    
    def find_tax_loss_harvesting_opportunities(
        self,
        holdings: Dict[str, Dict],
        wash_sale_exclusions: List[str] = None,
    ) -> List[Dict]:
        """
        Find tax-loss harvesting opportunities.
        
        Args:
            holdings: {symbol: {quantity, cost_basis, current_price}}
            wash_sale_exclusions: Symbols to exclude (purchased in last 30 days)
            
        Returns:
            List of harvesting opportunities
        """
        opportunities = []
        wash_sale_exclusions = wash_sale_exclusions or []
        
        for symbol, data in holdings.items():
            if symbol in wash_sale_exclusions:
                continue
            
            quantity = Decimal(str(data.get('quantity', 0)))
            cost_basis = Decimal(str(data.get('cost_basis', 0)))
            current_price = Decimal(str(data.get('current_price', 0)))
            
            if quantity <= 0 or cost_basis <= 0:
                continue
            
            current_value = quantity * current_price
            unrealized_loss = current_value - cost_basis
            loss_percent = (unrealized_loss / cost_basis) * 100
            
            # Only consider significant losses
            if unrealized_loss < -100:  # At least $100 loss
                # Calculate tax savings
                tax_savings = abs(unrealized_loss) * self.SHORT_TERM_RATE
                
                # Suggest replacement asset (similar but not identical)
                replacement = self._suggest_replacement(symbol)
                
                opportunities.append({
                    'symbol': symbol,
                    'quantity': float(quantity),
                    'cost_basis': float(cost_basis),
                    'current_price': float(current_price),
                    'current_value': float(current_value),
                    'unrealized_loss': float(unrealized_loss),
                    'loss_percent': float(loss_percent),
                    'estimated_tax_savings': float(tax_savings),
                    'replacement_symbol': replacement,
                    'wash_sale_safe': True,
                })
        
        # Sort by tax savings (highest first)
        opportunities.sort(key=lambda x: x['estimated_tax_savings'], reverse=True)
        
        logger.info(f"Found {len(opportunities)} tax-loss harvesting opportunities")
        return opportunities
    
    def _suggest_replacement(self, symbol: str) -> str:
        """Suggest a replacement asset for tax-loss harvesting."""
        # Simple replacement mapping (in production, use correlation analysis)
        replacements = {
            'BTC': 'WBTC',
            'ETH': 'stETH',
            'SOL': 'mSOL',
            'BNB': 'CAKE',
            'ADA': 'DOT',
            'XRP': 'ALGO',
            'DOGE': 'SHIB',
            'DOT': 'KSM',
            'AVAX': 'FTM',
            'LINK': 'BAND',
        }
        
        # Get base symbol without quote
        base = symbol.split('-')[0] if '-' in symbol else symbol
        return replacements.get(base, f'{base}_alt')
    
    def generate_tax_report(
        self,
        tax_lots: List[Dict],
        tax_year: int,
    ) -> Dict:
        """Generate a comprehensive tax report."""
        total_proceeds = Decimal('0')
        total_cost_basis = Decimal('0')
        total_gain_loss = Decimal('0')
        
        short_term_proceeds = Decimal('0')
        short_term_gain_loss = Decimal('0')
        long_term_proceeds = Decimal('0')
        long_term_gain_loss = Decimal('0')
        
        for lot in tax_lots:
            disposition_date = lot.get('disposition_date', '')
            if not disposition_date:
                continue
            
            try:
                year = int(disposition_date[:4])
                if year != tax_year:
                    continue
            except (ValueError, IndexError):
                continue
            
            proceeds = Decimal(str(lot.get('proceeds', 0)))
            cost_basis = Decimal(str(lot.get('cost_basis', 0)))
            gain_loss = Decimal(str(lot.get('gain_loss', 0)))
            
            total_proceeds += proceeds
            total_cost_basis += cost_basis
            total_gain_loss += gain_loss
            
            if lot.get('is_long_term'):
                long_term_proceeds += proceeds
                long_term_gain_loss += gain_loss
            else:
                short_term_proceeds += proceeds
                short_term_gain_loss += gain_loss
        
        # Calculate tax liability
        short_term_tax = max(short_term_gain_loss * self.SHORT_TERM_RATE, Decimal('0'))
        long_term_tax = max(long_term_gain_loss * self.LONG_TERM_RATE, Decimal('0'))
        total_tax = short_term_tax + long_term_tax
        
        return {
            'tax_year': tax_year,
            'total_proceeds': float(total_proceeds),
            'total_cost_basis': float(total_cost_basis),
            'total_gain_loss': float(total_gain_loss),
            'short_term_proceeds': float(short_term_proceeds),
            'short_term_gain_loss': float(short_term_gain_loss),
            'short_term_tax': float(short_term_tax),
            'long_term_proceeds': float(long_term_proceeds),
            'long_term_gain_loss': float(long_term_gain_loss),
            'long_term_tax': float(long_term_tax),
            'total_estimated_tax': float(total_tax),
            'effective_tax_rate': float(total_tax / total_proceeds * 100) if total_proceeds > 0 else 0,
        }
