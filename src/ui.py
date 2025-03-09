"""
UI components for the Pseudo Developer application.

This module contains the UI layout and component setup for the chat application.
"""

import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QTextEdit, QPushButton, QLineEdit, QLabel,
                           QStatusBar, QSplitter)
from PyQt5.QtCore import Qt

class ChatWindowUI:
    """
    UI component class for the chat window.
    
    This class handles the UI layout and components, separating the view
    from the business logic.
    """
    
    def __init__(self, parent_window):
        """
        Initialize the UI components for the chat window.
        
        Args:
            parent_window: The parent window that will contain these UI components
        """
        self.parent = parent_window
        self.init_ui()
        
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
        self.parent.setWindowTitle('Pseudo Developer')
        self.parent.setMinimumSize(1000, 800)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.parent.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Project directory input area
        dir_container = QWidget()
        dir_layout = QHBoxLayout(dir_container)
        
        dir_label = QLabel('Project Directory:')
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText('Enter project directory path...')
        
        save_button = QPushButton('Save')
        save_button.clicked.connect(self.parent.save_project_directory)
        
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
        send_button.clicked.connect(self.parent.send_message)
        
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(send_button)
        layout.addWidget(input_container)

        # Status bar for notifications
        self.status_bar = QStatusBar()
        self.parent.setStatusBar(self.status_bar)
    
    def show_status_message(self, message, timeout=5000):
        """
        Show a message in the status bar that automatically clears after timeout.
        
        Args:
            message (str): The message to display
            timeout (int): How long to display the message in milliseconds
        """
        self.status_bar.showMessage(message, timeout)
    
    def clear_message_input(self):
        """Clear the message input field."""
        self.message_input.clear()
    
    def get_message_input(self):
        """Get the text from the message input field."""
        return self.message_input.toPlainText().strip()
    
    def get_directory_input(self):
        """Get the text from the directory input field."""
        return self.dir_input.text().strip()
    
    def update_chat_display(self, messages):
        """
        Update the chat display with the given messages.
        
        Args:
            messages: List of (role, message) tuples to display
        """
        self.chat_display.clear()
        for role, message in messages:
            if not message:  # Skip None messages
                continue
                
            if role == "user":
                self.chat_display.append(f'You: {message}\n')
            else:
                self.chat_display.append(f'AI: {message}\n')
    
    def append_command_output(self, text):
        """
        Append text to the command output display.
        
        Args:
            text (str): The text to append
        """
        self.cmd_display.append(text)