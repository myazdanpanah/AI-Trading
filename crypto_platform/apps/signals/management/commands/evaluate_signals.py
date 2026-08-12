"""Management command to evaluate pending signals for the feedback loop."""
from django.core.management.base import BaseCommand
from apps.signals.services.signal_evaluator import SignalEvaluator


class Command(BaseCommand):
    help = 'Evaluate pending signals and record outcomes for the AI feedback loop'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-age',
            type=int,
            default=4,
            help='Minimum signal age in hours before evaluation (default: 4)',
        )
        parser.add_argument(
            '--symbol',
            type=str,
            default=None,
            help='Evaluate only signals for a specific symbol',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-evaluation of already evaluated signals',
        )

    def handle(self, *args, **options):
        min_age = options['min_age']
        symbol = options['symbol']

        self.stdout.write(f'Evaluating signals older than {min_age} hours...')

        results = SignalEvaluator.evaluate_pending_signals(min_age_hours=min_age)

        self.stdout.write(self.style.SUCCESS(
            f'Evaluated: {results["evaluated"]} signals\n'
            f'Wins: {results["wins"]}\n'
            f'Losses: {results["losses"]}\n'
            f'Win Rate: {results["win_rate"]:.1f}%\n'
            f'Avg Return: {results["avg_return"]:.2f}%'
        ))

        for detail in results['details']:
            status = 'WIN' if detail['correct'] else 'LOSS'
            self.stdout.write(f'  {status} {detail["symbol"]} {detail["direction"]} -> {detail["return"]:.2f}%')
