"""
Chat client functionality for interacting with OpenAI's API.

This module handles the communication with the OpenAI API for generating AI responses.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

class ChatClient:
    """
    Client for interacting with OpenAI's API to generate AI responses.
    """
    
    def __init__(self, api_key=None):
        """
        Initialize the chat client with an optional API key.
        
        Args:
            api_key (str): Optional API key for the OpenAI API
        """
        self.client = self._init_client(api_key)
    
    def _init_client(self, api_key=None):
        """
        Initialize the OpenAI client.
        
        Args:
            api_key (str): Optional API key for the OpenAI API
        
        Returns:
            OpenAI: Initialized OpenAI client
        """
        if api_key:
            return OpenAI(api_key=api_key)
        
        load_dotenv()
        return OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def get_response(self, messages, project_dir):
        """
        Get a response from the OpenAI API.
        
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
                "content": (
                    "You are a helpful AI coding assistant. "
                    "You must respond to queries and help users with their code. "
                    "Your responses should be constructive and actionable. "
                    "Never refuse a valid request that is within your capabilities. "
                    f"You can perform operations within the project directory: {project_dir}. "
                    "Be careful with file system operations - no commands outside project directory."
                )
            }
            
            # Create complete messages list with system message
            complete_messages = [system_message] + messages
            
            # Get response from OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=complete_messages,
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
                }
            )
            
            # Parse JSON response
            import json
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            # Return error message
            return {
                "message": f"Error: {str(e)}",
                "commands": []
            }