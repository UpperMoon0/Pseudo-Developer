"""
Chat client functionality for interacting with Google's Gemini API.

This module handles the communication with the Gemini API for generating AI responses.
"""

import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

class ChatClient:
    """
    Client for interacting with Google's Gemini API to generate AI responses.
    """

    def __init__(self, api_key=None):
        """
        Initialize the chat client with an optional API key.
        
        Args:
            api_key (str): Optional API key for the Gemini API
        """
        self.client = self._init_client(api_key)

    def _init_client(self, api_key=None):
        """
        Initialize the Gemini client.
        
        Args:
            api_key (str): Optional API key for the Gemini API
        
        Returns:
            genai.GenerativeModel: Initialized Gemini client
        """
        if api_key:
            genai.configure(api_key=api_key)
        else:
            load_dotenv()
            genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        
        return genai.GenerativeModel('gemini-1.5-flash')

    def get_response(self, messages, project_dir):
        """
        Get a response from the Gemini API.
        
        Args:
            messages (list): List of message objects with 'role' and 'content' properties
            project_dir (str): The project directory path to include in system message
            
        Returns:
            dict: Parsed JSON response from the API, or error message
        """
        try:
            # Add system message with project directory information
            system_message = {
                "role": "system",
                "parts": [
                    {
                        "text": (
                            "You are a helpful AI coding assistant. "
                            "You must respond to queries and help users with their code. "
                            "Your responses should be constructive and actionable. "
                            "Never refuse a valid request that is within your capabilities. "
                            f"You can perform operations within the project directory: {project_dir}. "
                            "Be careful with file system operations - no commands outside project directory."
                        )
                    }
                ]
            }

            # Create complete messages list with system message
            complete_messages = [system_message] + messages

            # Get response from Gemini
            response = self.client.generate_content(
                complete_messages,
                generation_config={
                    "response_mime_type": "application/json",
                    "response_schema": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "The main response message to display to the user"
                            },
                            "commands": {
                                "type": "array",
                                "description": "List of PowerShell commands to execute sequentially. Must be safe and within project directory.",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "command": {
                                            "type": "string",
                                            "description": "PowerShell command to execute"
                                        },
                                        "description": {
                                            "type": "string",
                                            "description": "Brief description of what the command does"
                                        }
                                    },
                                    "required": ["command", "description"],
                                    "additionalProperties": False
                                }
                            }
                        },
                        "required": ["message", "commands"],
                        "additionalProperties": False
                    }
                }
            )

            # Parse JSON response
            return json.loads(response.text)

        except Exception as e:
            # Return error message
            return {
                "message": f"Error: {str(e)}",
                "commands": []
            }