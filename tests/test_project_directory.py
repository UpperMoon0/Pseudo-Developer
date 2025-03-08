"""Tests for project directory functionality."""
import pytest
import os
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QMessageBox
from src.main import ChatWindow

@pytest.fixture
def chat_window(app):
    """Fixture to create ChatWindow instance."""
    return ChatWindow()

@pytest.fixture
def temp_dir(tmp_path):
    """Fixture to create a temporary directory for testing."""
    return tmp_path

def test_save_project_directory_empty_path(chat_window):
    """Test that trying to save an empty directory path shows error in status bar."""
    chat_window.dir_input.setText("")
    chat_window.save_project_directory()
    assert chat_window.status_bar.currentMessage().startswith("Error: Please enter")

def test_save_project_directory_success(chat_window, temp_dir):
    """Test successful creation and saving of project directory."""
    test_path = os.path.join(temp_dir, "test_project")
    chat_window.dir_input.setText(str(test_path))
    chat_window.save_project_directory()
    
    assert os.path.exists(test_path)
    assert chat_window.status_bar.currentMessage().startswith("Success: Directory saved")
    assert chat_window.project_dir == os.path.abspath(test_path)

def test_save_project_directory_error(chat_window, monkeypatch):
    """Test handling of directory creation error."""
    def mock_makedirs(*args, **kwargs):
        raise PermissionError("Access denied")
    monkeypatch.setattr(os, "makedirs", mock_makedirs)
    
    chat_window.dir_input.setText("/invalid/path")
    chat_window.save_project_directory()
    
    assert chat_window.status_bar.currentMessage().startswith("Error: Failed to create")