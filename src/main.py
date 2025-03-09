"""
Main entry point for the Pseudo Developer application.

This module initializes the application and connects the UI, command execution,
and chat client modules together.
"""

import sys
import os
from collections import deque
from PyQt5.QtWidgets import QApplication, QMainWindow
from src.ui import ChatWindowUI
from src.command_executor import CommandExecutor
from src.chat_client import ChatClient

class ChatWindow(QMainWindow):
    """
    Main window class for the chat application.
    
    This class orchestrates the UI, command execution, and chat functionalities by
    delegating to specialized modules.
    """

    def __init__(self, openai_client=None):
        """
        Initialize the chat window and setup components.
        
        Args:
            openai_client: Optional OpenAI client for testing
        """
        super().__init__()
        self.message_history = deque(maxlen=20)  # Store last 20 messages
        self.project_dir = None
        
        # Initialize components
        self.ui = ChatWindowUI(self)
        self.command_executor = CommandExecutor()
        self.chat_client = ChatClient(api_key=openai_client.api_key if openai_client else None)

    def save_project_directory(self):
        """
        Save the project directory path and create the directory if it doesn't exist.
        Shows status message to indicate success or failure.
        """
        dir_path = self.ui.get_directory_input()
        if not dir_path:
            self.ui.show_status_message("Error: Please enter a directory path")
            return

        try:
            # Create directory if it doesn't exist
            os.makedirs(dir_path, exist_ok=True)
            self.project_dir = os.path.abspath(dir_path)
            
            # Update command executor with project directory
            self.command_executor.set_project_dir(self.project_dir)
            
            self.ui.show_status_message(f"Success: Directory saved - {dir_path}")
        except Exception as e:
            self.ui.show_status_message(f"Error: Failed to create directory - {str(e)}")

    def add_to_history(self, user_message, ai_message):
        """
        Add a message pair to the history.
        
        Args:
            user_message (str): The user's message
            ai_message (str): The AI's response message
        """
        self.message_history.append(("user", user_message))
        self.message_history.append(("assistant", ai_message))
        self.ui.update_chat_display(self.message_history)

    def process_command_results(self, results):
        """
        Process command execution results and display them in the UI.
        
        Args:
            results (list): List of command result dictionaries
        """
        for i, result in enumerate(results):
            command = result['command']
            description = result['description']
            is_safe = result['is_safe']
            stdout = result['stdout']
            stderr = result['stderr']
            
            # Display command and description
            self.ui.append_command_output(f'[{i+1}/{len(results)}] {description}')
            self.ui.append_command_output(f'Command: {command}\n')
            
            # Display execution results
            if is_safe:
                if stdout:
                    self.ui.append_command_output(f'Output:\n{stdout}\n')
                if stderr:
                    self.ui.append_command_output(f'Error:\n{stderr}\n')
            else:
                self.ui.append_command_output(f'Command rejected for security reasons - cannot execute command: "{command}"\n')
            
            # Add separator
            self.ui.append_command_output('-' * 40 + '\n')
    
    def send_message(self):
        """
        Handle sending user message and receiving AI response.
        """
        user_message = self.ui.get_message_input()
        if not user_message:
            return

        if not self.project_dir:
            self.ui.append_command_output("Please set a project directory first before sending messages.\n")
            return

        # Add user message to history and display
        self.add_to_history(user_message, None)  # AI message will be added later
        
        try:
            # Build messages list from history (excluding the last user message which we just added)
            messages = []
            for role, content in list(self.message_history)[:-1]:
                if content is not None:  # Skip None messages
                    messages.append({"role": role, "content": content})
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Get response from chat client
            response_data = self.chat_client.get_response(messages, self.project_dir)
            
            # Update AI message in history
            self.message_history[-1] = ("assistant", response_data["message"])
            self.ui.update_chat_display(self.message_history)
            
            # Process commands
            commands = response_data.get('commands', [])
            if commands:
                self.ui.append_command_output(f'Executing {len(commands)} commands sequentially:\n')
                
                # Execute commands and process results
                results = self.command_executor.execute_commands(commands)
                self.process_command_results(results)
            else:
                self.ui.append_command_output('No commands to execute\n')
                self.ui.append_command_output('-' * 40 + '\n')
                
        except Exception as e:
            error_msg = f'Error: {str(e)}'
            self.message_history[-1] = ("assistant", error_msg)
            self.ui.update_chat_display(self.message_history)
            self.ui.append_command_output(error_msg + '\n')
            self.ui.append_command_output('-' * 40 + '\n')
        
        # Clear input field
        self.ui.clear_message_input()

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