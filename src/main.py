"""
Modern AI Chat Application using PyQt5 and OpenAI API.
This module implements a desktop chat interface for interacting with OpenAI's GPT model.
"""

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QTextEdit, QPushButton, QLineEdit, QLabel,
                           QStatusBar, QMessageBox)
from openai import OpenAI
from dotenv import load_dotenv

class ChatWindow(QMainWindow):
    """
    Main window class for the chat application.
    
    This class handles the UI layout and chat functionality, including:
    - Message input and display
    - OpenAI API integration
    """

    def __init__(self, openai_client=None):
        """
        Initialize the chat window and setup UI components.
        
        Args:
            openai_client: Optional OpenAI client for testing
        """
        super().__init__()
        self.init_ui()
        self.client = openai_client if openai_client else self.init_openai()
        self.project_dir = None  # Will store the selected project directory

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
        - Message input area
        - Send button
        - Status bar for notifications
        """
        self.setWindowTitle('Pseudo Developer')
        self.setMinimumSize(800, 600)
        
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
        
        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)
        
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

    def send_message(self):
        """
        Handle sending user message and receiving AI response.
        
        The AI response will be formatted as JSON with two parts:
        - message: The text response to display
        - command: Optional PowerShell command to execute
        """
        user_message = self.message_input.toPlainText().strip()
        if not user_message:
            return

        if not self.project_dir:
            self.chat_display.append("Please set a project directory first before sending messages.\n")
            return

        # Display user message
        self.chat_display.append(f'You: {user_message}\n')
        
        try:
            # Get AI response with specific JSON format instruction using schema
            response = self.client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {"role": "system", "content": (
                        "You are a helpful AI coding assistant. "
                        "You must respond to queries and help users with their code. "
                        "Your responses should be constructive and actionable. "
                        "Never refuse a valid request that is within your capabilities. "
                        f"You can perform operations within the project directory: {self.project_dir}. "
                        "Be careful with file system operations - no commands outside project directory."
                    )},
                    {"role": "user", "content": user_message}
                ],
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
                # Display AI response message part
                self.chat_display.append(f'AI: {response_data["message"]}\n')
                
                command = response_data.get('command', '').strip()
                if command:
                    if self.is_safe_command(command):
                        import subprocess
                        # Change working directory to project directory before executing command
                        process = subprocess.Popen(
                            ['powershell', '-NoProfile', '-NonInteractive', '-Command', command],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            shell=True,
                            cwd=self.project_dir
                        )
                        stdout, stderr = process.communicate()
                        self.chat_display.append(f'Executing command: {command}\n')
                        if stdout:
                            self.chat_display.append(f'Output:\n{stdout}\n')
                        if stderr:
                            self.chat_display.append(f'Error:\n{stderr}\n')
                    else:
                        self.chat_display.append(f'Command rejected for security reasons - cannot execute command: "{command}"\n')
                
            except json.JSONDecodeError:
                self.chat_display.append(f'AI: {ai_message}\n')
                self.chat_display.append('Warning: Response was not in valid JSON format\n')
            except Exception as e:
                self.chat_display.append(f'Error executing command: {str(e)}\n')
                
        except Exception as e:
            self.chat_display.append(f'Error: {str(e)}\n')
        
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