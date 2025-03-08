"""Central test runner for all test suites."""
import os
import sys
import pytest

if __name__ == '__main__':
    # Add project root to Python path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    
    pytest.main(['--verbose', '--cov=src', '--cov-report=term-missing'])