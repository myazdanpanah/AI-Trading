"""Data validation layer for market data quality checks."""
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Validation severity levels."""
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    severity: ValidationSeverity
    field: str
    message: str
    value: Optional[str] = None


@dataclass
class ValidationReport:
    """Complete validation report."""
    data_type: str
    symbol: str
    exchange: str
    timestamp: datetime
    results: List[ValidationResult]
    passed: bool = True

    def add_result(self, result: ValidationResult):
        self.results.append(result)
        if not result.is_valid and result.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
            self.passed = False

    def to_dict(self) -> Dict:
        return {
            'data_type': self.data_type,
            'symbol': self.symbol,
            'exchange': self.exchange,
            'timestamp': self.timestamp.isoformat(),
            'passed': self.passed,
            'errors': [r.message for r in self.results if not r.is_valid],
            'warnings': [r.message for r in self.results if r.severity == ValidationSeverity.WARNING],
        }


class DataValidator:
    """Validates market data quality."""

    # Validation thresholds
    MAX_PRICE_CHANGE_PERCENT = Decimal('50')  # Max 50% price change in single candle
    MAX_VOLUME_SPIKE_MULTIPLIER = Decimal('100')  # Max 100x volume spike
    MIN_LIQUIDITY_USD = Decimal('10000')  # Minimum $10k liquidity
    MAX_SPREAD_PERCENT = Decimal('5')  # Max 5% spread
    MAX_FUNDING_RATE = Decimal('0.01')  # Max 1% funding rate
    MAX_DATA_AGE_HOURS = 24  # Max age for historical data

    @classmethod
    def validate_candle(cls, candle_data: Dict) -> ValidationReport:
        """Validate candle/OHLCV data."""
        report = ValidationReport(
            data_type='candle',
            symbol=candle_data.get('symbol', ''),
            exchange=candle_data.get('exchange', ''),
            timestamp=datetime.now(),
        )

        # Check required fields
        required_fields = ['open', 'high', 'low', 'close', 'volume', 'timestamp']
        for field in required_fields:
            if field not in candle_data or candle_data[field] is None:
                report.add_result(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    field=field,
                    message=f'Missing required field: {field}',
                ))

        if not report.passed:
            return report

        open_price = Decimal(str(candle_data['open']))
        high = Decimal(str(candle_data['high']))
        low = Decimal(str(candle_data['low']))
        close = Decimal(str(candle_data['close']))
        volume = Decimal(str(candle_data['volume']))

        # Validate price relationships
        if high < low:
            report.add_result(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                field='high/low',
                message=f'High ({high}) is less than Low ({low})',
            ))

        # High must be >= open and close
        if high < open_price:
            report.add_result(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                field='high',
                message=f'High ({high}) is less than Open ({open_price})',
            ))

        if high < close:
            report.add_result(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                field='high',
                message=f'High ({high}) is less than Close ({close})',
            ))

        # Low must be <= open and close
        if low > open_price:
            report.add_result(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                field='low',
                message=f'Low ({low}) is greater than Open ({open_price})',
            ))

        if low > close:
            report.add_result(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                field='low',
                message=f'Low ({low}) is greater than Close ({close})',
            ))

        # Check for zero/negative prices
        for field_name, value in [('open', open_price), ('high', high), ('low', low), ('close', close)]:
            if value <= 0:
                report.add_result(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    field=field_name,
                    message=f'{field_name} must be positive, got {value}',
                ))

        # Check for zero/negative volume
        if volume < 0:
            report.add_result(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                field='volume',
                message=f'Volume cannot be negative, got {volume}',
            ))

        # Check for extreme price changes
        if open_price > 0:
            price_change = abs(close - open_price) / open_price * 100
            if price_change > cls.MAX_PRICE_CHANGE_PERCENT:
                report.add_result(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    field='price_change',
                    message=f'Extreme price change: {price_change:.2f}%',
                    value=str(price_change),
                ))

        return report

    @classmethod
    def validate_orderbook(cls, orderbook_data: Dict) -> ValidationReport:
        """Validate order book data."""
        report = ValidationReport(
            data_type='orderbook',
            symbol=orderbook_data.get('symbol', ''),
            exchange=orderbook_data.get('exchange', ''),
            timestamp=datetime.now(),
        )

        bids = orderbook_data.get('bids', [])
        asks = orderbook_data.get('asks', [])

        # Check if order book is empty
        if not bids and not asks:
            report.add_result(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.WARNING,
                field='orderbook',
                message='Empty order book',
            ))
            return report

        # Validate bid/ask prices are positive
        for i, bid in enumerate(bids[:5]):
            price = Decimal(str(bid.get('price', 0))) if isinstance(bid, dict) else Decimal(str(bid[0] if isinstance(bid, (list, tuple)) else 0))
            if price <= 0:
                report.add_result(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    field=f'bids[{i}]',
                    message=f'Invalid bid price: {price}',
                ))

        for i, ask in enumerate(asks[:5]):
            price = Decimal(str(ask.get('price', 0))) if isinstance(ask, dict) else Decimal(str(ask[0] if isinstance(ask, (list, tuple)) else 0))
            if price <= 0:
                report.add_result(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    field=f'asks[{i}]',
                    message=f'Invalid ask price: {price}',
                ))

        # Check spread
        if bids and asks:
            best_bid = Decimal(str(bids[0].get('price', 0) if isinstance(bids[0], dict) else bids[0][0]))
            best_ask = Decimal(str(asks[0].get('price', 0) if isinstance(asks[0], dict) else asks[0][0]))
            
            if best_bid > 0:
                spread = best_ask - best_bid
  
