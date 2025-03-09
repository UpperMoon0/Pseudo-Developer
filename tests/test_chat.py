"""Tests for the chat application's core functionality."""
import pytest
import os
import json
from unittest.mock import MagicMock, patch
from src.main import ChatWindow

@pytest.fixture
def mock_openai_client():
    """Fixture for mocked OpenAI client."""
    mock_client = MagicMock()
    return mock_client

@pytest.fixture
def chat_window(app, mock_openai_client):
    """Fixture to create ChatWindow instance with mocked OpenAI client."""
    return ChatWindow(openai_client=mock_openai_client)

@pytest.fixture
def temp_dir(tmpdir):
    """Fixture to create a temporary directory for testing."""
    return tmpdir

@pytest.fixture
def chat_window_with_project(chat_window, temp_dir):
    """Fixture to create ChatWindow instance with project directory set."""
    test_path = os.path.join(temp_dir, "test_project")
    chat_window.ui.dir_input.setText(str(test_path))
    chat_window.save_project_directory()
    return chat_window

@pytest.fixture
def mock_popen():
    """Fixture for mocked subprocess.Popen"""
    with patch('subprocess.Popen') as mock:
        yield mock

def test_message_input_clear_on_send(chat_window_with_project):
    """Test that message input is cleared after sending."""
    test_message = "Test message"
    chat_window_with_project.ui.message_input.setText(test_message)
    chat_window_with_project.send_message()
    assert chat_window_with_project.ui.message_input.toPlainText() == ""

def test_empty_message_not_sent(chat_window_with_project):
    """Test that empty messages are not sent."""
    chat_window_with_project.ui.message_input.setText("")
    initial_content = chat_window_with_project.ui.chat_display.toPlainText()
    chat_window_with_project.send_message()
    assert chat_window_with_project.ui.chat_display.toPlainText() == initial_content

def test_whitespace_message_not_sent(chat_window_with_project):
    """Test that whitespace-only messages are not sent."""
    chat_window_with_project.ui.message_input.setText("   \n   ")
    initial_content = chat_window_with_project.ui.chat_display.toPlainText()
    chat_window_with_project.send_message()
    assert chat_window_with_project.ui.chat_display.toPlainText() == initial_content

def test_successful_message_send_and_display(chat_window_with_project, monkeypatch):
    """Test successful message sending and response display."""
    # Mock the chat_client.get_response method
    mock_response = {"message": "Test AI response", "commands": []}
    
    def mock_get_response(*args, **kwargs):
        return mock_response
        
    monkeypatch.setattr(chat_window_with_project.chat_client, "get_response", mock_get_response)
    
    # Send test message
    test_message = "Test message"
    chat_window_with_project.ui.message_input.setText(test_message)
    chat_window_with_project.send_message()
    
    # Verify message flow
    display_content = chat_window_with_project.ui.chat_display.toPlainText()
    assert f"You: {test_message}" in display_content
    assert "AI:" in display_content
    assert "Test AI response" in display_content

def test_api_error_handling_and_display(chat_window_with_project, monkeypatch):
    """Test error handling and error message display."""
    def mock_get_response(*args, **kwargs):
        raise Exception("API Error")
        
    monkeypatch.setattr(chat_window_with_project.chat_client, "get_response", mock_get_response)
    
    # Send test message
    test_message = "Test message"
    chat_window_with_project.ui.message_input.setText(test_message)
    chat_window_with_project.send_message()
    
    # Verify error handling
    display_content = chat_window_with_project.ui.chat_display.toPlainText()
    assert f"You: {test_message}" in display_content
    assert "Error:" in display_content

def test_message_history_preservation(chat_window_with_project, monkeypatch):
    """Test that chat history is preserved when sending multiple messages."""
    responses = [
        {"message": "Response 1", "commands": []},
        {"message": "Response 2", "commands": []}
    ]
    response_iter = iter(responses)
    
    def mock_get_response(*args, **kwargs):
        return next(response_iter)
        
    monkeypatch.setattr(chat_window_with_project.chat_client, "get_response", mock_get_response)
    
    # First message
    chat_window_with_project.ui.message_input.setText("Message 1")
    chat_window_with_project.send_message()
    
    # Second message
    chat_window_with_project.ui.message_input.setText("Message 2")
    chat_window_with_project.send_message()
    
    # Verify chat history
    display_content = chat_window_with_project.ui.chat_display.toPlainText()
    assert "You: Message 1" in display_content
    assert "Response 1" in display_content
    assert "You: Message 2" in display_content
    assert "Response 2" in display_content

def test_command_execution(chat_window_with_project, monkeypatch):
    """Test execution of commands from AI response."""
    # Mock the chat_client.get_response method
    mock_response = {
        "message": "Running a command", 
        "commands": [
            {"command": "dir", "description": "List directory contents"}
        ]
    }
    
    def mock_get_response(*args, **kwargs):
        return mock_response
        
    # Mock the command executor
    mock_results = [{
        "command": "dir",
        "description": "List directory contents",
        "stdout": "Directory listing output",
        "stderr": "",
        "is_safe": True
    }]
    
    def mock_execute_commands(*args, **kwargs):
        return mock_results
        
    monkeypatch.setattr(chat_window_with_project.chat_client, "get_response", mock_get_response)
    monkeypatch.setattr(chat_window_with_project.command_executor, "execute_commands", mock_execute_commands)
    
    # Send test message
    chat_window_with_project.ui.message_input.setText("Run a command")
    chat_window_with_project.send_message()
    
    # Verify command execution and output display
    cmd_content = chat_window_with_project.ui.cmd_display.toPlainText()
    assert "Executing 1 commands sequentially" in cmd_content
    assert "List directory contents" in cmd_content
    assert "Command: dir" in cmd_content
    assert "Output:\nDirectory listing output" in cmd_content

def test_unsafe_command_not_executed(chat_window_with_project, monkeypatch):
    """Test that unsafe commands are not executed."""
    # Mock the chat_client.get_response method
    unsafe_command = "format C:"
    mock_response = {
        "message": "Running unsafe command", 
        "commands": [
            {"command": unsafe_command, "description": "Format drive"}
        ]
    }
    
    def mock_get_response(*args, **kwargs):
        return mock_response
        
    # Mock the command executor
    mock_results = [{
        "command": unsafe_command,
        "description": "Format drive",
        "stdout": None,
        "stderr": None,
        "is_safe": False
    }]
    
    def mock_execute_commands(*args, **kwargs):
        return mock_results
        
    monkeypatch.setattr(chat_window_with_project.chat_client, "get_response", mock_get_response)
    monkeypatch.setattr(chat_window_with_project.command_executor, "execute_commands", mock_execute_commands)
    
    # Send test message
    chat_window_with_project.ui.message_input.setText("Run unsafe command")
    chat_window_with_project.send_message()
    
    # Verify command rejection
    cmd_content = chat_window_with_project.ui.cmd_display.toPlainText()
    assert "Command rejected for security reasons" in cmd_content
    assert unsafe_command in cmd_content

def test_no_project_dir_message(chat_window):
    """Test that messages can't be sent without setting project directory."""
    test_message = "Test message"
    chat_window.ui.message_input.setText(test_message)
    chat_window.send_message()
    
    output_content = chat_window.ui.cmd_display.toPlainText()
    assert "Please set a project directory first" in output_content

def test_save_project_dir_sets_absolute_path(chat_window, temp_dir):
    """Test that saving project directory stores absolute path."""
    test_path = os.path.join(temp_dir, "test_project")
    chat_window.ui.dir_input.setText(str(test_path))
    chat_window.save_project_directory()
    
    assert chat_window.project_dir == os.path.abspath(test_path)
    # Also verify CommandExecutor was updated
    assert chat_window.command_executor.project_dir == os.path.abspath(test_path)

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

def test_save_project_directory_error(chat_window, monkeypatch):
    """Test handling of directory creation error."""
    # Mock os.makedirs to raise an error
    def mock_makedirs(*args, **kwargs):
        raise PermissionError("Access denied")
    monkeypatch.setattr(os, "makedirs", mock_makedirs)
    
    chat_window.ui.dir_input.setText("/invalid/path")
    chat_window.save_project_directory()
    
    assert chat_window.ui.status_bar.currentMessage().startswith("Error: Failed to create")

@pytest.mark.parametrize("command,expected_safe", [
    ("dir", True),
    ("type test.txt", True),
    ("del test.txt", True),
    ("rm file.txt", True),
    ("move file.txt newfile.txt", True),
    ("ren oldname.txt newname.txt", True),
    ("rmdir test", True),
    ("rd temp", True),
    ("format C:", False),
    ("..\\file.txt", False),
    ("~\\file.txt", False),
    ("C:\\outside\\path", False),
])
def test_is_safe_command(chat_window_with_project, command, expected_safe):
    """Test command safety validation with various commands."""
    # Set project directory for consistent testing
    chat_window_with_project.command_executor.set_project_dir("C:/test/project")
    assert chat_window_with_project.command_executor.is_safe_command(command) == expected_safe

def test_command_error_display(chat_window_with_project, monkeypatch):
    """Test that command errors are properly displayed."""
    # Mock chat client and command executor
    mock_response = {
        "message": "Running command with error",
        "commands": [
            {"command": "invalid_cmd", "description": "Run invalid command"}
        ]
    }
    
    def mock_get_response(*args, **kwargs):
        return mock_response
        
    # Mock command execution with error
    mock_results = [{
        "command": "invalid_cmd",
        "description": "Run invalid command",
        "stdout": "",
        "stderr": "Command not found",
        "is_safe": True
    }]
    
    def mock_execute_commands(*args, **kwargs):
        return mock_results
        
    monkeypatch.setattr(chat_window_with_project.chat_client, "get_response", mock_get_response)
    monkeypatch.setattr(chat_window_with_project.command_executor, "execute_commands", mock_execute_commands)
    
    # Send test message
    chat_window_with_project.ui.message_input.setText("Run command with error")
    chat_window_with_project.send_message()
    
    # Verify error display
    cmd_content = chat_window_with_project.ui.cmd_display.toPlainText()
    assert "Run invalid command" in cmd_content
    assert "Command: invalid_cmd" in cmd_content
    assert "Error:\nCommand not found" in cmd_content

def test_message_history_limit(chat_window_with_project, monkeypatch):
    """Test that message history is limited to maxlen messages."""
    # Create a mock response that always returns the same data
    mock_response = {"message": "Response", "commands": []}
    
    def mock_get_response(*args, **kwargs):
        return mock_response
        
    monkeypatch.setattr(chat_window_with_project.chat_client, "get_response", mock_get_response)
    
    # Get the current maxlen
    maxlen = chat_window_with_project.message_history.maxlen
    
    # Send more messages than the maximum
    num_extra_messages = 5
    for i in range(maxlen + num_extra_messages):
        chat_window_with_project.ui.message_input.setText(f"Message {i}")
        chat_window_with_project.send_message()
    
    # Verify message history length is limited to maxlen
    assert len(chat_window_with_project.message_history) == maxlen

def test_multiple_commands_executed_sequentially(chat_window_with_project, monkeypatch):
    """Test that multiple commands are executed sequentially."""
    # Mock the chat_client.get_response method with multiple commands
    mock_response = {
        "message": "Running multiple commands", 
        "commands": [
            {"command": "dir", "description": "List directory contents"},
            {"command": "echo Hello", "description": "Print hello message"}
        ]
    }
    
    def mock_get_response(*args, **kwargs):
        return mock_response
        
    # Mock command execution results
    mock_results = [
        {
            "command": "dir",
            "description": "List directory contents",
            "stdout": "Directory listing output",
            "stderr": "",
            "is_safe": True
        },
        {
            "command": "echo Hello",
            "description": "Print hello message",
            "stdout": "Hello",
            "stderr": "",
            "is_safe": True
        }
    ]
    
    def mock_execute_commands(*args, **kwargs):
        return mock_results
        
    monkeypatch.setattr(chat_window_with_project.chat_client, "get_response", mock_get_response)
    monkeypatch.setattr(chat_window_with_project.command_executor, "execute_commands", mock_execute_commands)
    
    # Send test message
    chat_window_with_project.ui.message_input.setText("Run multiple commands")
    chat_window_with_project.send_message()
    
    # Verify all commands were executed and displayed
    cmd_content = chat_window_with_project.ui.cmd_display.toPlainText()
    assert "Executing 2 commands sequentially" in cmd_content
    assert "List directory contents" in cmd_content
    assert "Print hello message" in cmd_content
    assert "Output:\nDirectory listing output" in cmd_content
    assert "Output:\nHello" in cmd_content