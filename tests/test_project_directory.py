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
    chat_window.ui.dir_input.setText("")
    chat_window.save_project_directory()
    assert chat_window.ui.status_bar.currentMessage().startswith("Error: Please enter")

def test_save_project_directory_success(chat_window, temp_dir):
    """Test successful creation and saving of project directory."""
    test_path = os.path.join(temp_dir, "test_project")
    chat_window.ui.dir_input.setText(str(test_path))
    chat_window.save_project_directory()
    
    assert os.path.exists(test_path)
    assert chat_window.ui.status_bar.currentMessage().startswith("Success: Directory saved")
    assert chat_window.project_dir == os.path.abspath(test_path)
    # Verify the command executor was updated with the project directory
    assert chat_window.command_executor.project_dir == os.path.abspath(test_path)

def test_save_project_directory_error(chat_window, monkeypatch):
    """Test handling of directory creation error."""
    def mock_makedirs(*args, **kwargs):
        raise PermissionError("Access denied")
    monkeypatch.setattr(os, "makedirs", mock_makedirs)
    
    chat_window.ui.dir_input.setText("/invalid/path")
    chat_window.save_project_directory()
    
    assert chat_window.ui.status_bar.currentMessage().startswith("Error: Failed to create")
    
def test_project_dir_needed_for_command_execution(chat_window, monkeypatch):
    """Test that commands require a project directory to be set."""
    # Create a command executor with no project dir set
    assert chat_window.project_dir is None
    
    # Test that commands are considered unsafe when no project dir is set
    test_command = "dir"
    assert not chat_window.command_executor.is_safe_command(test_command)
    
    # Test direct command execution
    stdout, stderr, is_safe = chat_window.command_executor.execute_command(test_command)
    assert not is_safe
    assert stdout is None
    assert stderr is None