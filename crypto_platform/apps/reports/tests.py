"""Tests for reports app."""
from django.test import TestCase
from .models import Report
from datetime import datetime


class ReportModelsTest(TestCase):
    def test_report_creation(self):
        report = Report.objects.create(
            report_type='daily_market',
            title='Daily Market Report',
            period_start=datetime.now(),
            period_end=datetime.now()
        )
        self.assertEqual(report.report_type, 'daily_market')
        self.assertEqual(report.title, 'Daily Market Report')
