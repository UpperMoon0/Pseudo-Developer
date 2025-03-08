"""
Modern AI Chat Application using PyQt5 and OpenAI API.
This module implements a desktop chat interface for interacting with OpenAI's GPT model.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton
import openai
from dotenv import load_dotenv

class ChatWindow(QMainWindow):
    """
    Main window class for the chat application.
    
    This class handles the UI layout and chat functionality, including:
    - Message input and display
    - OpenAI API integration
    """

    def __init__(self):
        """Initialize the chat window and setup UI components."""
        super().__init__()
        self.init_ui()
        self.init_openai()

    def init_openai(self):
        """Initialize OpenAI API configuration from environment variables."""
        load_dotenv()
        openai.api_key = os.getenv('OPENAI_API_KEY')

    def init_ui(self):
        """
        Setup the user interface components.
        
        Initializes:
        - Window properties
        - Chat display area
        - Message input area
        - Send button
        """
        self.setWindowTitle('Modern AI Chat')
        self.setMinimumSize(800, 600)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)
        
        # Input area
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

    def send_message(self):
        """
        Handle sending user message and receiving AI response.
        
        This method:
        1. Gets the user message from input
        2. Displays the message
        3. Sends it to OpenAI API
        4. Displays the AI response
        5. Handles any errors that occur
        """
        user_message = self.message_input.toPlainText().strip()
        if not user_message:
            return

        # Display user message
        self.chat_display.append(f'You: {user_message}\n')
        
        try:
            # Get AI response
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": user_message}]
            )
            ai_message = response.choices[0].message.content
            
            # Display AI response
            self.chat_display.append(f'AI: {ai_message}\n')
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