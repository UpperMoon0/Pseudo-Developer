"""
Modern AI Chat Application using PyQt5 and OpenAI API.
This module implements a desktop chat interface for interacting with OpenAI's GPT model.
"""

import sys
import os
from collections import deque
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QTextEdit, QPushButton, QLineEdit, QLabel,
                           QStatusBar, QMessageBox, QSplitter)
from PyQt5.QtCore import Qt
from openai import OpenAI
from dotenv import load_dotenv

class ChatWindow(QMainWindow):
    """
    Main window class for the chat application.
    
    This class handles the UI layout and chat functionality, including:
    - Message input and display
    - Command output display
    - Message history management
    - OpenAI API integration
    """

    def __init__(self, openai_client=None):
        """
        Initialize the chat window and setup UI components.
        
        Args:
            openai_client: Optional OpenAI client for testing
        """
        super().__init__()
        self.message_history = deque(maxlen=20)  # Store last 10 pairs of messages
        self.client = openai_client if openai_client else self.init_openai()
        self.project_dir = None  # Will store the selected project directory
        self.init_ui()

    def init_openai(self):
        """Initialize OpenAI API configuration from environment variables."""
        load_dotenv()
        return OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    def init_ui(self):
        """
        Setup the user interface components.
        
        Initializes:
        - Window properties
        - Project directory input
        - Chat display area
        - Command output display area
        - Message input area
        - Send button
        - Status bar for notifications
        """
        self.setWindowTitle('Pseudo Developer')
        self.setMinimumSize(1000, 800)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Project directory input area
        dir_container = QWidget()
        dir_layout = QHBoxLayout(dir_container)
        
        dir_label = QLabel('Project Directory:')
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText('Enter project directory path...')
        
        save_button = QPushButton('Save')
        save_button.clicked.connect(self.save_project_directory)
        
        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(save_button)
        layout.addWidget(dir_container)
        
        # Create a splitter for chat and command outputs
        splitter = QSplitter(Qt.Vertical)
        
        # Chat display area
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        chat_label = QLabel('Chat History')
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        chat_layout.addWidget(chat_label)
        chat_layout.addWidget(self.chat_display)
        chat_container.setLayout(chat_layout)
        
        # Command output area
        cmd_container = QWidget()
        cmd_layout = QVBoxLayout(cmd_container)
        cmd_label = QLabel('Command Output')
        self.cmd_display = QTextEdit()
        self.cmd_display.setReadOnly(True)
        cmd_layout.addWidget(cmd_label)
        cmd_layout.addWidget(self.cmd_display)
        cmd_container.setLayout(cmd_layout)
        
        # Add both displays to splitter
        splitter.addWidget(chat_container)
        splitter.addWidget(cmd_container)
        splitter.setStretchFactor(0, 2)  # Chat display gets more space
        splitter.setStretchFactor(1, 1)  # Command output gets less space
        
        layout.addWidget(splitter)
        
        # Message input area
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        
        self.message_input = QTextEdit()
        self.message_input.setFixedHeight(70)
        
        send_button = QPushButton('Send')
        send_button.setFixedSize(70, 70)
        send_button.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(send_button)
        layout.addWidget(input_container)

        # Status bar for notifications
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def show_status_message(self, message, timeout=5000):
        """Show a message in the status bar that automatically clears after timeout."""
        self.status_bar.showMessage(message, timeout)

    def save_project_directory(self):
        """
        Save the project directory path and create the directory if it doesn't exist.
        Shows status message to indicate success or failure.
        """
        dir_path = self.dir_input.text().strip()
        if not dir_path:
            self.show_status_message("Error: Please enter a directory path")
            return

        try:
            # Create directory if it doesn't exist
            os.makedirs(dir_path, exist_ok=True)
            self.project_dir = os.path.abspath(dir_path)  # Store absolute path
            self.show_status_message(f"Success: Directory saved - {dir_path}")
        except Exception as e:
            self.show_status_message(f"Error: Failed to create directory - {str(e)}")

    def is_safe_command(self, command):
        """
        Check if a command is safe to execute by verifying it only accesses the project directory.
        Only blocks the 'format' command and ensures all operations stay within project directory.
        
        Args:
            command (str): The command to check
            
        Returns:
            bool: True if the command is safe, False otherwise
        """
        if not self.project_dir:
            return False
            
        # Block the format command as it's too dangerous
        cmd_parts = command.lower().split()
        if not cmd_parts:
            return False
            
        if 'format' in cmd_parts[0]:
            return False
            
        # Check if the command tries to navigate outside project directory using .. or ~
        if '..' in command or '~' in command:
            return False
            
        # Check if any absolute paths in the command are within project directory or its subdirectories
        parts = command.split()
        for part in parts:
            if ':' in part:  # Windows absolute path
                # Remove any quotes around the path
                clean_part = part.strip('"\'')
                abs_path = os.path.abspath(clean_part)
                project_path = os.path.abspath(self.project_dir)
                
                # Check if the path is the project directory or a subdirectory of it
                try:
                    rel_path = os.path.relpath(abs_path, project_path)
                    if rel_path.startswith('..'):
                        return False
                except ValueError:
                    # relpath raises ValueError if the paths are on different drives
                    return False
                    
        return True

    def add_to_history(self, user_message, ai_message):
        """
        Add a message pair to the history.
        
        Args:
            user_message (str): The user's message
            ai_message (str): The AI's response message
        """
        self.message_history.append(("user", user_message))
        self.message_history.append(("assistant", ai_message))
        self.update_chat_display()

    def update_chat_display(self):
        """Update the chat display with the current message history."""
        self.chat_display.clear()
        for role, message in self.message_history:
            if role == "user":
                self.chat_display.append(f'You: {message}\n')
            else:
                self.chat_display.append(f'AI: {message}\n')

    def send_message(self):
        """
        Handle sending user message and receiving AI response.
        """
        user_message = self.message_input.toPlainText().strip()
        if not user_message:
            return

        if not self.project_dir:
            self.chat_display.append("Please set a project directory first before sending messages.\n")
            return

        # Add user message to history and display
        self.add_to_history(user_message, None)  # AI message will be added later
        
        try:
            # Build messages list including history
            messages = [
                {"role": "system", "content": (
                    "You are a helpful AI coding assistant. "
                    "You must respond to queries and help users with their code. "
                    "Your responses should be constructive and actionable. "
                    "Never refuse a valid request that is within your capabilities. "
                    f"You can perform operations within the project directory: {self.project_dir}. "
                    "Be careful with file system operations - no commands outside project directory."
                )}
            ]
            
            # Add message history (excluding the last user message which we'll add next)
            for role, content in list(self.message_history)[:-1]:
                if content is not None:  # Skip None messages
                    messages.append({"role": role, "content": content})
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Get AI response with specific JSON format instruction using schema
            response = self.client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=messages,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "assistant_response",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "message": {
                                    "type": "string",
                                    "description": "The main response message to display to the user"
                                },
                                "command": {
                                    "type": "string",
                                    "description": "Optional PowerShell command to execute. Must be safe and within project directory."
                                }
                            },
                            "required": ["message", "command"],
                            "additionalProperties": False
                        }
                    }
                }
            )
            ai_message = response.choices[0].message.content
            
            try:
                import json
                response_data = json.loads(ai_message)
                # Update AI message in history
                self.message_history[-1] = ("assistant", response_data["message"])
                self.update_chat_display()
                
                command = response_data.get('command', '').strip()
                if command:
                    if self.is_safe_command(command):
                        import subprocess
                        process = subprocess.Popen(
                            ['powershell', '-NoProfile', '-NonInteractive', '-Command', command],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            shell=True,
                            cwd=self.project_dir
                        )
                        stdout, stderr = process.communicate()
                        self.cmd_display.append(f'Executing command: {command}\n')
                        if stdout:
                            self.cmd_display.append(f'Output:\n{stdout}\n')
                        if stderr:
                            self.cmd_display.append(f'Error:\n{stderr}\n')
                        self.cmd_display.append('-' * 40 + '\n')  # Add separator
                    else:
                        self.cmd_display.append(f'Command rejected for security reasons - cannot execute command: "{command}"\n')
                        self.cmd_display.append('-' * 40 + '\n')
                
            except json.JSONDecodeError:
                # Add raw message to history and display
                self.message_history[-1] = ("assistant", ai_message)
                self.update_chat_display()
                self.cmd_display.append('Warning: Response was not in valid JSON format\n')
                self.cmd_display.append('-' * 40 + '\n')
            except Exception as e:
                error_msg = f'Error executing command: {str(e)}'
                self.cmd_display.append(error_msg + '\n')
                self.cmd_display.append('-' * 40 + '\n')
                
        except Exception as e:
            error_msg = f'Error: {str(e)}'
            self.message_history[-1] = ("assistant", error_msg)
            self.update_chat_display()
            self.cmd_display.append(error_msg + '\n')
            self.cmd_display.append('-' * 40 + '\n')
        
        # Clear input field
        self.message_input.clear()

def main():
    """Initialize and run the chat application."""
    app = QApplication(sys.argv)
    
    # Load and apply stylesheet
    style_path = os.path.join(os.path.dirname(__file__), 'styles.qss')
    with open(style_path, 'r') as f:
        app.setStyleSheet(f.read())
    
    window = ChatWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()