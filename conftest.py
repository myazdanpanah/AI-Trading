"""Pytest configuration for Crypto AI Signal Platform."""
import sys
from pathlib import Path

# Add project root and crypto_platform to Python path
# This ensures 'apps.xxx' and 'crypto_platform.apps.xxx' patterns both work
ROOT_DIR = Path(__file__).resolve().parent
CRYPTO_PLATFORM_DIR = ROOT_DIR / 'crypto_platform'

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(CRYPTO_PLATFORM_DIR) not in sys.path:
    sys.path.insert(0, str(CRYPTO_PLATFORM_DIR))

# Configure Django settings before any Django imports
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crypto_platform.settings')
