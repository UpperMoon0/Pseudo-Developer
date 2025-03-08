"""Test configuration and shared fixtures."""
import os
import sys
import pytest
from PyQt5.QtWidgets import QApplication

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Store QApplication reference to prevent garbage collection
_qapp = None

@pytest.fixture(scope="session")
def app():
    """Fixture to create QApplication instance."""
    global _qapp
    _qapp = QApplication([])
    return _qapp