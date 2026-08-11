#!/usr/bin/env python
"""Test runner script for Crypto AI Signal Platform.

This script sets up the correct Python path before running Django tests,
resolving the Windows path handling issues with the standard test runner.

Usage:
    python run_tests.py                          # Run all tests
    python run_tests.py apps.feedback             # Run feedback app tests
    python run_tests.py apps.feedback.test_integration  # Run specific test module
"""
import os
import sys
from pathlib import Path

# Set up paths before any Django imports
ROOT_DIR = Path(__file__).resolve().parent
CRYPTO_PLATFORM_DIR = ROOT_DIR / 'crypto_platform'

# Add paths in correct order
for path in [str(ROOT_DIR), str(CRYPTO_PLATFORM_DIR)]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crypto_platform.settings')


def main():
    """Run Django tests with proper configuration."""
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # Build test command
    argv = ['run_tests.py', 'test'] + sys.argv[1:]
    
    # Add verbosity if not specified
    if '--verbosity' not in ' '.join(argv):
        argv.append('--verbosity=2')
    
    execute_from_command_line(argv)


if __name__ == '__main__':
    main()
