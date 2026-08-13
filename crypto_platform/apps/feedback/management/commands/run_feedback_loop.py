"""Management command to run the 6-hour BTC feedback loop."""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Run the 6-hour BTC feedback loop'

    def handle(self, *args, **options):
        from apps.feedback.services.btc_feedback_loop import BTCFeedbackLoop
        
        self.stdout.write('Running 6-hour BTC feedback loop...')
        results = BTCFeedbackLoop.run()
        
        if results['status'] == 'success':
            self.stdout.write(self.style.SUCCESS(
                f'Feedback loop completed in {results.get("execution_time_seconds", 0)}s'
            ))
            self.stdout.write(f'  Insights: {len(results.get("insights", []))}')
        else:
            self.stdout.write(self.style.ERROR(
                f'Feedback loop failed: {results.get("error", "unknown error")}'
            ))
