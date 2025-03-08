"""Tests for project directory management functionality."""
import pytest
import os
from unittest.mock import MagicMock
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

def test_save_project_directory_empty_path(chat_window, monkeypatch):
    """Test that trying to save an empty directory path shows warning."""
    mock_warning = MagicMock()
    monkeypatch.setattr(QMessageBox, "warning", mock_warning)
    
    chat_window.dir_input.setText("")
    chat_window.save_project_directory()
    
    mock_warning.assert_called_once()
    assert "Please enter a directory path" in mock_warning.call_args[0][2]

def test_save_project_directory_success(chat_window, temp_dir, monkeypatch):
    """Test successful creation and saving of project directory."""
    mock_info = MagicMock()
    monkeypatch.setattr(QMessageBox, "information", mock_info)
    
    test_path = os.path.join(temp_dir, "test_project")
    chat_window.dir_input.setText(str(test_path))
    chat_window.save_project_directory()
    
    assert os.path.exists(test_path)
    mock_info.assert_called_once()
    assert str(test_path) in mock_info.call_args[0][2]  # Check the message part

def test_save_project_directory_error(chat_window, monkeypatch):
    """Test handling of directory creation error."""
    mock_critical = MagicMock()
    monkeypatch.setattr(QMessageBox, "critical", mock_critical)
    
    # Mock os.makedirs to raise an error
    def mock_makedirs(*args, **kwargs):
        raise PermissionError("Access denied")
    
    monkeypatch.setattr(os, "makedirs", mock_makedirs)
    
    chat_window.dir_input.setText("/invalid/path")
    chat_window.save_project_directory()
    
    mock_critical.assert_called_once()
    assert "Failed to create directory" in mock_critical.call_args[0][2]  # Check the message part