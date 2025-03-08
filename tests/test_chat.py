"""Tests for the chat application's core functionality."""
import pytest
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication
from src.main import ChatWindow

# Store QApplication reference to prevent garbage collection
_qapp = None

@pytest.fixture
def app():
    """Fixture to create QApplication instance."""
    global _qapp
    _qapp = QApplication([])
    return _qapp

@pytest.fixture
def chat_window(app):
    """Fixture to create ChatWindow instance."""
    return ChatWindow()

def test_message_input_clear_on_send(chat_window):
    """Test that message input is cleared after sending."""
    test_message = "Test message"
    chat_window.message_input.setText(test_message)
    chat_window.send_message()
    assert chat_window.message_input.toPlainText() == ""

def test_empty_message_not_sent(chat_window):
    """Test that empty messages are not sent."""
    chat_window.message_input.setText("")
    initial_content = chat_window.chat_display.toPlainText()
    chat_window.send_message()
    assert chat_window.chat_display.toPlainText() == initial_content

def test_whitespace_message_not_sent(chat_window):
    """Test that whitespace-only messages are not sent."""
    chat_window.message_input.setText("   \n   ")
    initial_content = chat_window.chat_display.toPlainText()
    chat_window.send_message()
    assert chat_window.chat_display.toPlainText() == initial_content

@patch('openai.chat.completions.create')
def test_successful_message_send_and_display(mock_openai, chat_window):
    """Test successful message sending and response display."""
    # Mock OpenAI response
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Test AI response"
    mock_openai.return_value = mock_response
    
    # Send test message
    test_message = "Test message"
    chat_window.message_input.setText(test_message)
    chat_window.send_message()
    
    # Verify message flow
    display_content = chat_window.chat_display.toPlainText()
    assert f"You: {test_message}" in display_content
    assert "AI: Test AI response" in display_content

@patch('openai.chat.completions.create')
def test_api_error_handling_and_display(mock_openai, chat_window):
    """Test error handling and error message display."""
    # Mock API error
    mock_openai.side_effect = Exception("API Error")
    
    # Send test message
    test_message = "Test message"
    chat_window.message_input.setText(test_message)
    chat_window.send_message()
    
    # Verify error handling
    display_content = chat_window.chat_display.toPlainText()
    assert f"You: {test_message}" in display_content
    assert "Error: API Error" in display_content

@patch('openai.chat.completions.create')
def test_message_history_preservation(mock_openai, chat_window):
    """Test that chat history is preserved when sending multiple messages."""
    # First message
    mock_openai.return_value = MagicMock(choices=[MagicMock(message=MagicMock(content="Response 1"))])
    chat_window.message_input.setText("Message 1")
    chat_window.send_message()
    
    # Second message
    mock_openai.return_value = MagicMock(choices=[MagicMock(message=MagicMock(content="Response 2"))])
    chat_window.message_input.setText("Message 2")
    chat_window.send_message()
    
    # Verify chat history
    display_content = chat_window.chat_display.toPlainText()
    assert "You: Message 1" in display_content
    assert "AI: Response 1" in display_content
    assert "You: Message 2" in display_content
    assert "AI: Response 2" in display_content