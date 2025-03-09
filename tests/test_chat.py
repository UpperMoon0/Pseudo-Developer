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
    window = ChatWindow(openai_client=mock_openai_client)
    window._in_test = True
    return window

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

def test_file_write_operation(chat_window_with_project, temp_dir):
    """Test writing content to a file using echo command."""
    test_file = os.path.join(temp_dir, "test_project", "test.txt")
    test_content = "Hello, World!"
    command = f'echo {test_content} > {test_file}'
    
    # Execute command
    stdout, stderr, is_safe = chat_window_with_project.command_executor.execute_command(command)
    
    # Verify command execution
    assert is_safe is True
    assert stdout == "File written successfully"
    assert stderr is None
    
    # Verify file contents
    with open(test_file, 'r') as f:
        content = f.read()
        assert content.strip() == test_content

def test_large_file_write_operation(chat_window_with_project, temp_dir):
    """Test writing large content to a file in chunks."""
    test_file = os.path.join(temp_dir, "test_project", "large.txt")
    # Create content larger than chunk size (8KB)
    test_content = "Large content! " * 1000  # Much larger than CHUNK_SIZE
    
    success, error = chat_window_with_project.command_executor.safe_write_file(test_file, test_content)
    
    # Verify write operation
    assert success is True
    assert error is None
    
    # Verify file contents
    with open(test_file, 'r') as f:
        content = f.read()
        assert content == test_content

def test_file_read_operation(chat_window_with_project, temp_dir):
    """Test reading content from a file."""
    test_file = os.path.join(temp_dir, "test_project", "read_test.txt")
    test_content = "Test content for reading"
    
    # Create test file
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    # Read file using safe_read_file
    content, error = chat_window_with_project.command_executor.safe_read_file(test_file)
    
    # Verify read operation
    assert error is None
    assert content == test_content

def test_file_copy_operation(chat_window_with_project, temp_dir):
    """Test copying a file within project directory."""
    src_file = os.path.join(temp_dir, "test_project", "source.txt")
    dst_file = os.path.join(temp_dir, "test_project", "destination.txt")
    test_content = "Content to be copied"
    
    # Create source file
    with open(src_file, 'w') as f:
        f.write(test_content)
    
    # Copy file using safe_copy_file
    success, error = chat_window_with_project.command_executor.safe_copy_file(src_file, dst_file)
    
    # Verify copy operation
    assert success is True
    assert error is None
    assert os.path.exists(dst_file)
    
    # Verify file contents
    with open(dst_file, 'r') as f:
        content = f.read()
        assert content == test_content

def test_file_operations_outside_project(chat_window_with_project, temp_dir):
    """Test that file operations outside project directory are blocked."""
    outside_file = os.path.join(temp_dir, "outside.txt")
    test_content = "This should not be written"
    
    # Test write operation
    success, error = chat_window_with_project.command_executor.safe_write_file(outside_file, test_content)
    assert success is False
    assert "outside project directory" in error
    assert not os.path.exists(outside_file)
    
    # Test read operation
    content, error = chat_window_with_project.command_executor.safe_read_file(outside_file)
    assert content is None
    assert "outside project directory" in error
    
    # Test copy operation (both source and destination outside)
    dst_file = os.path.join(temp_dir, "outside_copy.txt")
    success, error = chat_window_with_project.command_executor.safe_copy_file(outside_file, dst_file)
    assert success is False
    assert "outside project directory" in error

def test_directory_creation(chat_window_with_project, temp_dir):
    """Test creating nested directories within project directory."""
    test_dir = os.path.join(temp_dir, "test_project", "nested", "subdirectory")
    test_file = os.path.join(test_dir, "test.txt")
    test_content = "Test content in nested directory"
    
    # Write file to nested directory (should create directories)
    success, error = chat_window_with_project.command_executor.safe_write_file(test_file, test_content)
    
    # Verify directory creation and file write
    assert success is True
    assert error is None
    assert os.path.exists(test_dir)
    assert os.path.exists(test_file)
    
    # Verify file contents
    with open(test_file, 'r') as f:
        content = f.read()
        assert content == test_content

def test_unicode_content_handling(chat_window_with_project, temp_dir):
    """Test handling of unicode content in file operations."""
    test_file = os.path.join(temp_dir, "test_project", "unicode.txt")
    test_content = "Hello, 世界! 👋 🌍"  # Unicode text with emojis
    
    # Write unicode content
    success, error = chat_window_with_project.command_executor.safe_write_file(test_file, test_content)
    assert success is True
    assert error is None
    
    # Read back and verify content
    content, error = chat_window_with_project.command_executor.safe_read_file(test_file)
    assert error is None
    assert content == test_content

def test_path_security(chat_window_with_project, temp_dir):
    """Test path security checks for various path formats."""
    test_paths = [
        ("../outside.txt", False),  # Parent directory
        ("./inside.txt", True),     # Current directory
        ("~/file.txt", False),      # Home directory
        ("normal.txt", True),       # Simple filename
        ("subfolder/file.txt", True), # Nested path
        ("C:/absolute/path.txt", False), # Absolute path
        ("\x00malicious.txt", False),  # Null byte injection
    ]
    
    for path, expected_safe in test_paths:
        full_path = os.path.join(temp_dir, "test_project", path)
        assert chat_window_with_project.command_executor.is_path_in_project(path) == expected_safe

def test_file_write_with_quotes(chat_window_with_project, temp_dir):
    """Test writing content to a file with quotes in the content."""
    test_file = os.path.join(temp_dir, "test_project", "quoted.txt")
    test_cases = [
        ('echo "Hello World" > ' + test_file, "Hello World"),
        ("echo 'print(\"Hello\")' > " + test_file, 'print("Hello")'),
        ('echo "value = \'test\'" > ' + test_file, "value = 'test'")
    ]
    
    for command, expected in test_cases:
        # Execute command
        stdout, stderr, is_safe = chat_window_with_project.command_executor.execute_command(command)
        
        # Verify command execution
        assert is_safe is True
        assert stdout == "File written successfully"
        assert stderr is None
        
        # Verify file contents
        with open(test_file, 'r') as f:
            content = f.read()
            assert content.strip() == expected

def test_file_write_with_here_string(chat_window_with_project, temp_dir):
    """Test writing multi-line content using PowerShell here-string syntax."""
    test_file = os.path.join(temp_dir, "test_project", "multiline.py")
    command = """$code = @'
def hello():
    print("Hello, World!")
    return 42

if __name__ == "__main__":
    result = hello()
    print(f"Result: {result}")
'@ > """ + test_file
    
    # Execute command
    stdout, stderr, is_safe = chat_window_with_project.command_executor.execute_command(command)
    
    # Verify command execution
    assert is_safe is True
    assert stdout == "File written successfully"
    assert stderr is None
    
    # Verify file contents
    with open(test_file, 'r') as f:
        content = f.read()
        expected = '''def hello():
    print("Hello, World!")
    return 42

if __name__ == "__main__":
    result = hello()
    print(f"Result: {result}")'''
        assert content.strip() == expected.strip()

def test_file_write_with_set_content(chat_window_with_project, temp_dir):
    """Test writing multi-line content using PowerShell Set-Content command."""
    test_file = os.path.join(temp_dir, "test_project", "set_content_test.py")
    content = '''"""
def hello():
    print("Hello, World!")
    return 42

if __name__ == "__main__":
    result = hello()
    print(f"Result: {result}")
"""'''
    command = f'Set-Content -Path {test_file} -Value {content}'
    
    # Execute command
    stdout, stderr, is_safe = chat_window_with_project.command_executor.execute_command(command)
    
    # Verify command execution
    assert is_safe is True
    assert stdout == "File written successfully"
    assert stderr is None
    
    # Verify file contents
    with open(test_file, 'r') as f:
        written_content = f.read()
        expected = '''def hello():
    print("Hello, World!")
    return 42

if __name__ == "__main__":
    result = hello()
    print(f"Result: {result}")'''
        assert written_content.strip() == expected.strip()

def test_file_write_with_set_content_python_script(chat_window_with_project, temp_dir):
    """Test writing Python script with Set-Content, verifying quote and newline handling."""
    test_file = os.path.join(temp_dir, "test_project", "test_script.py")
    # Use raw string to handle backslashes and escaping properly
    command = r'''Set-Content -Path {} -Value @"
# Sample Python script
def calculate_sum(numbers):
    """Returns the sum of a list of numbers."""
    return sum(numbers)

def main():
    numbers = [1, 2, 3, 4, 5]
    result = calculate_sum(numbers)
    print(f"The sum is: {{result}}")

if __name__ == '__main__':
    main()
"@'''.format(test_file)
    
    # Execute command
    stdout, stderr, is_safe = chat_window_with_project.command_executor.execute_command(command)
    
    # Verify command execution
    assert is_safe is True
    assert stdout == "File written successfully"
    assert stderr is None
    
    # Verify file contents and proper handling of quotes and docstrings
    with open(test_file, 'r') as f:
        content = f.read()
        assert '"""Returns the sum of a list of numbers."""' in content
        assert "if __name__ == '__main__':" in content
        assert 'print(f"The sum is: {result}")' in content

def test_file_write_with_set_content_single_line(chat_window_with_project, temp_dir):
    """Test writing content using PowerShell Set-Content command with single line format."""
    test_file = os.path.join(temp_dir, "test_project", "single_line.py")
    
    # Single line format that should work more reliably
    command = f'Set-Content -Path {test_file} -Value "print(\'Hello from single line\')"'
    
    # Execute command
    stdout, stderr, is_safe = chat_window_with_project.command_executor.execute_command(command)
    
    # Verify command execution
    assert is_safe is True
    assert stdout == "File written successfully"
    assert stderr is None
    
    # Verify file contents
    with open(test_file, 'r') as f:
        content = f.read()
        assert content.strip() == "print('Hello from single line')"

def test_file_write_with_add_content(chat_window_with_project, temp_dir):
    """Test writing multi-line content using PowerShell Add-Content command."""
    test_file = os.path.join(temp_dir, "test_project", "add_content_test.py")
    
    # First create empty file
    command_create = f'New-Item -Path {test_file} -ItemType File'
    stdout, stderr, is_safe = chat_window_with_project.command_executor.execute_command(command_create)
    assert is_safe is True
    
    # Then add content
    command_add = f'''Add-Content -Path {test_file} -Value @"
def calculate_primes(n):
    primes = []
    num = 2
    while len(primes) < n:
        if all(num % p != 0 for p in primes):
            primes.append(num)
        num += 1
    return primes

if __name__ == '__main__':
    print('First 20 primes:', calculate_primes(20))
"@'''
    
    # Execute command
    stdout, stderr, is_safe = chat_window_with_project.command_executor.execute_command(command_add)
    
    # Verify command execution
    assert is_safe is True
    assert stdout == "File written successfully"
    assert stderr is None
    
    # Verify file contents
    with open(test_file, 'r') as f:
        content = f.read().strip()
        assert 'def calculate_primes(n):' in content
        assert 'print(\'First 20 primes:\'' in content
        assert content.count('\n') >= 8  # Check that line breaks are preserved