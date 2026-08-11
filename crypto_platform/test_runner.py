"""Custom Django test runner for Windows compatibility."""
import sys
from pathlib import Path


def setup_test_environment():
    """Ensure proper path setup before Django initialization."""
    root_dir = Path(__file__).resolve().parent.parent
    crypto_platform_dir = root_dir / 'crypto_platform'
    
    paths_to_add = [str(root_dir), str(crypto_platform_dir)]
    
    for path in paths_to_add:
        if path not in sys.path:
            sys.path.insert(0, path)


# Run setup immediately when module is imported
setup_test_environment()
