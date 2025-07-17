"""
Chat client functionality for interacting with Google's Gemini API.

This module handles the communication with the Gemini API for generating AI responses.
"""

import os
import json
import platformdirs
import google.generativeai as genai
from google.api_core import exceptions

class ChatClient:
    """
    Client for interacting with Google's Gemini API to generate AI responses.
    """

    def __init__(self):
        """
        Initialize the chat client.
        """
        self.keys_path = self._get_api_key_path()
        self.api_keys = self._load_keys()
        self.current_key_index = 0
        self.client = self._init_client()

    def _get_api_key_path(self):
        """
        Get the path to the API key file.
        """
        app_dir = platformdirs.user_data_dir("PseudoDeveloper", "NsTut")
        os.makedirs(app_dir, exist_ok=True)
        return os.path.join(app_dir, "gemini-api-keys.json")

    def _load_keys(self):
        """
        Load API keys from the JSON file.
        """
        if os.path.exists(self.keys_path):
            with open(self.keys_path, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return []
        return []

    def _save_keys(self):
        """
        Save API keys to the JSON file.
        """
        with open(self.keys_path, 'w') as f:
            json.dump(self.api_keys, f, indent=4)

    def _init_client(self):
        """
        Initialize the Gemini client.
        """
        if not self.api_keys:
            return None
        
        genai.configure(api_key=self.api_keys[self.current_key_index])
        return genai.GenerativeModel('gemini-1.5-flash')

    def _cycle_key(self):
        """
        Cycle to the next API key.
        """
        if not self.api_keys:
            return False
        
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self.client = self._init_client()
        return True

    def get_response(self, messages, project_dir):
        """
        Get a response from the Gemini API.
        """
        if not self.client:
            return {"message": "Error: No API keys configured.", "commands": []}

        for _ in range(len(self.api_keys)):
            try:
                response = self.client.generate_content(
                    messages,
                    generation_config={
                        "response_mime_type": "application/json",
                        "response_schema": {
                            "type": "object",
                            "properties": {
                                "message": {"type": "string"},
                                "commands": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "command": {"type": "string"},
                                            "params": {"type": "object"}
                                        },
                                        "required": ["command"]
                                    }
                                }
                            },
                            "required": ["message", "commands"]
                        }
                    }
                )
                return json.loads(response.text)
            except exceptions.ResourceExhausted as e:
                if not self._cycle_key():
                    return {"message": f"Error: {str(e)}", "commands": []}
            except Exception as e:
                return {"message": f"Error: {str(e)}", "commands": []}
        
        return {"message": "Error: All API keys failed.", "commands": []}

    def get_api_keys(self):
        """
        Get the list of API keys.
        """
        return self.api_keys

    def add_api_key(self, key):
        """
        Add an API key.
        """
        if key not in self.api_keys:
            self.api_keys.append(key)
            self._save_keys()
            if len(self.api_keys) == 1:
                self.client = self._init_client()

    def remove_api_key(self, key):
        """
        Remove an API key.
        """
        if key in self.api_keys:
            self.api_keys.remove(key)
            self._save_keys()
            if not self.api_keys:
                self.client = None
            elif self.current_key_index >= len(self.api_keys):
                self.current_key_index = 0
                self.client = self._init_client()