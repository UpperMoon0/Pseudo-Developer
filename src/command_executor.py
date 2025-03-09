"""
Command execution functionality for Pseudo Developer application.

This module handles the safe execution of commands within the specified project directory.
"""

import os
import subprocess

class CommandExecutor:
    """
    Handles the execution of commands in a safe manner, restricted to the project directory.
    """
    
    def __init__(self, project_dir=None):
        """
        Initialize the command executor with an optional project directory.
        
        Args:
            project_dir (str): The project directory to execute commands within
        """
        self.project_dir = project_dir
    
    def set_project_dir(self, directory):
        """
        Set the project directory for command execution.
        
        Args:
            directory (str): The directory path to set
        """
        self.project_dir = directory
    
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
    
    def execute_command(self, command):
        """
        Execute a single command in the project directory if it's safe.
        
        Args:
            command (str): The command to execute
            
        Returns:
            tuple: (stdout, stderr, is_safe) output from the command execution and safety status
        """
        if not self.is_safe_command(command):
            return None, None, False
            
        process = subprocess.Popen(
            ['powershell', '-NoProfile', '-NonInteractive', '-Command', command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True,
            cwd=self.project_dir
        )
        stdout, stderr = process.communicate()
        return stdout, stderr, True
        
    def execute_commands(self, command_list):
        """
        Execute multiple commands sequentially and return their results.
        
        Args:
            command_list (list): List of command objects with 'command' and 'description' properties
            
        Returns:
            list: List of dictionaries with command information and execution results
        """
        results = []
        
        for cmd_obj in command_list:
            command = cmd_obj.get('command', '').strip()
            description = cmd_obj.get('description', 'No description provided')
            
            if command:
                stdout, stderr, is_safe = self.execute_command(command)
                
                results.append({
                    'command': command,
                    'description': description,
                    'stdout': stdout,
                    'stderr': stderr,
                    'is_safe': is_safe
                })
                
        return results