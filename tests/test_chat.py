"""Tests for the chat application's core functionality."""
import pytest
import os
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
    chat_window.dir_input.setText(str(test_path))
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
    chat_window_with_project.message_input.setText(test_message)
    chat_window_with_project.send_message()
    assert chat_window_with_project.message_input.toPlainText() == ""

def test_empty_message_not_sent(chat_window_with_project):
    """Test that empty messages are not sent."""
    chat_window_with_project.message_input.setText("")
    initial_content = chat_window_with_project.chat_display.toPlainText()
    chat_window_with_project.send_message()
    assert chat_window_with_project.chat_display.toPlainText() == initial_content

def test_whitespace_message_not_sent(chat_window_with_project):
    """Test that whitespace-only messages are not sent."""
    chat_window_with_project.message_input.setText("   \n   ")
    initial_content = chat_window_with_project.chat_display.toPlainText()
    chat_window_with_project.send_message()
    assert chat_window_with_project.chat_display.toPlainText() == initial_content

def test_successful_message_send_and_display(chat_window_with_project, mock_openai_client):
    """Test successful message sending and response display."""
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"message": "Test AI response", "command": ""}'
    mock_openai_client.chat.completions.create.return_value = mock_response
    
    # Send test message
    test_message = "Test message"
    chat_window_with_project.message_input.setText(test_message)
    chat_window_with_project.send_message()
    
    # Verify message flow
    display_content = chat_window_with_project.chat_display.toPlainText()
    assert f"You: {test_message}" in display_content
    assert "AI:" in display_content
    assert "Test AI response" in display_content

def test_api_error_handling_and_display(chat_window_with_project, mock_openai_client):
    """Test error handling and error message display."""
    mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
    
    # Send test message
    test_message = "Test message"
    chat_window_with_project.message_input.setText(test_message)
    chat_window_with_project.send_message()
    
    # Verify error handling
    display_content = chat_window_with_project.chat_display.toPlainText()
    assert f"You: {test_message}" in display_content
    assert "Error: API Error" in display_content

def test_message_history_preservation(chat_window_with_project, mock_openai_client):
    """Test that chat history is preserved when sending multiple messages."""
    # First message
    mock_response1 = MagicMock()
    mock_response1.choices[0].message.content = '{"message": "Response 1", "command": ""}'
    mock_openai_client.chat.completions.create.return_value = mock_response1
    chat_window_with_project.message_input.setText("Message 1")
    chat_window_with_project.send_message()
    
    # Second message
    mock_response2 = MagicMock()
    mock_response2.choices[0].message.content = '{"message": "Response 2", "command": ""}'
    mock_openai_client.chat.completions.create.return_value = mock_response2
    chat_window_with_project.message_input.setText("Message 2")
    chat_window_with_project.send_message()
    
    # Verify chat history
    display_content = chat_window_with_project.chat_display.toPlainText()
    assert "You: Message 1" in display_content
    assert "Response 1" in display_content
    assert "You: Message 2" in display_content
    assert "Response 2" in display_content

def test_json_response_format(mock_popen, chat_window_with_project, mock_openai_client):
    """Test handling of JSON formatted response with message and command."""
    # Setup mock client
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"message": "Test message", "command": "dir"}'
    mock_openai_client.chat.completions.create.return_value = mock_response
    
    # Setup mock process
    process_mock = MagicMock()
    process_mock.communicate.return_value = ("Directory listing", "")  # Mock stdout and stderr
    mock_popen.return_value = process_mock
    
    # Send test message
    chat_window_with_project.message_input.setText("Test command")
    chat_window_with_project.send_message()
    
    # Verify JSON parsing and command execution
    display_content = chat_window_with_project.chat_display.toPlainText()
    assert 'You: Test command' in display_content
    assert 'Test message' in display_content
    assert 'Executing command: dir' in display_content
    mock_popen.assert_called_once()

def test_invalid_json_response(chat_window_with_project, mock_openai_client):
    """Test handling of invalid JSON response."""
    # Setup mock client
    mock_response = MagicMock()
    mock_response.choices[0].message.content = 'Invalid JSON'
    mock_openai_client.chat.completions.create.return_value = mock_response
    
    # Send test message
    chat_window_with_project.message_input.setText("Test invalid JSON")
    chat_window_with_project.send_message()
    
    # Verify error handling
    display_content = chat_window_with_project.chat_display.toPlainText()
    assert 'You: Test invalid JSON' in display_content
    assert 'AI: Invalid JSON' in display_content
    assert 'Warning: Response was not in valid JSON format' in display_content

def test_empty_command_not_executed(mock_popen, chat_window_with_project, mock_openai_client):
    """Test that empty commands are not executed."""
    # Setup mock client
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"message": "Test message", "command": ""}'
    mock_openai_client.chat.completions.create.return_value = mock_response
    
    # Send test message
    chat_window_with_project.message_input.setText("Test empty command")
    chat_window_with_project.send_message()
    
    # Verify command not executed
    display_content = chat_window_with_project.chat_display.toPlainText()
    assert 'You: Test empty command' in display_content
    assert 'Test message' in display_content
    mock_popen.assert_not_called()

def test_no_project_dir_message(chat_window):
    """Test that messages can't be sent without setting project directory."""
    test_message = "Test message"
    chat_window.message_input.setText(test_message)
    chat_window.send_message()
    
    display_content = chat_window.chat_display.toPlainText()
    assert "Please set a project directory first" in display_content

def test_save_project_dir_sets_absolute_path(chat_window, temp_dir):
    """Test that saving project directory stores absolute path."""
    test_path = os.path.join(temp_dir, "test_project")
    chat_window.dir_input.setText(str(test_path))
    chat_window.save_project_directory()
    
    assert chat_window.project_dir == os.path.abspath(test_path)

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
    # Mock os.makedirs to raise an error
    def mock_makedirs(*args, **kwargs):
        raise PermissionError("Access denied")
    monkeypatch.setattr(os, "makedirs", mock_makedirs)
    
    chat_window.dir_input.setText("/invalid/path")
    chat_window.save_project_directory()
    
    assert chat_window.status_bar.currentMessage().startswith("Error: Failed to create")

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
    # Mock project directory for consistent testing
    chat_window_with_project.project_dir = "C:/test/project"
    assert chat_window_with_project.is_safe_command(command) == expected_safe

def test_unsafe_command_not_executed(mock_popen, chat_window_with_project, mock_openai_client):
    """Test that unsafe commands are not executed."""
    unsafe_command = "format C:"
    mock_response = MagicMock()
    mock_response.choices[0].message.content = f'{{"message": "Test", "command": "{unsafe_command}"}}'
    mock_openai_client.chat.completions.create.return_value = mock_response
    
    # Send test message
    chat_window_with_project.message_input.setText("Test unsafe command")
    chat_window_with_project.send_message()
    
    # Verify command was not executed
    display_content = chat_window_with_project.chat_display.toPlainText()
    assert "Command rejected for security reasons" in display_content
    assert f'"{unsafe_command}"' in display_content
    mock_popen.assert_not_called()

def test_command_output_display(mock_popen, chat_window_with_project, mock_openai_client):
    """Test that command output is properly displayed."""
    # Setup mock client and process
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"message": "Running directory listing", "command": "dir"}'
    mock_openai_client.chat.completions.create.return_value = mock_response
    
    # Mock process output
    process_mock = MagicMock()
    process_mock.communicate.return_value = ("Directory listing output", "")
    mock_popen.return_value = process_mock
    
    # Send test message
    chat_window_with_project.message_input.setText("List directory")
    chat_window_with_project.send_message()
    
    # Verify output display
    display_content = chat_window_with_project.chat_display.toPlainText()
    assert "Running directory listing" in display_content
    assert "Executing command: dir" in display_content
    assert "Output:\nDirectory listing output" in display_content

def test_command_error_display(mock_popen, chat_window_with_project, mock_openai_client):
    """Test that command errors are properly displayed."""
    # Setup mock client and process
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"message": "Attempting command", "command": "invalid_cmd"}'
    mock_openai_client.chat.completions.create.return_value = mock_response
    
    # Mock process error
    process_mock = MagicMock()
    process_mock.communicate.return_value = ("", "Command not found")
    mock_popen.return_value = process_mock
    
    # Send test message
    chat_window_with_project.message_input.setText("Run invalid command")
    chat_window_with_project.send_message()
    
    # Verify error display
    display_content = chat_window_with_project.chat_display.toPlainText()
    assert "Attempting command" in display_content
    assert "Executing command: invalid_cmd" in display_content
    assert "Error:\nCommand not found" in display_content