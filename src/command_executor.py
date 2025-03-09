"""
Command execution functionality for Pseudo Developer application.

This module handles the safe execution of commands within the specified project directory.
"""

import os
import subprocess
import shutil
import re
from pathlib import Path

class CommandExecutor:
    """
    Handles the execution of commands in a safe manner, restricted to the project directory.
    """
    
    CHUNK_SIZE = 8192  # 8KB chunks for file operations
    
    def __init__(self, project_dir=None):
        """
        Initialize the command executor with an optional project directory.
        
        Args:
            project_dir (str): The project directory to execute commands within
        """
        self.project_dir = project_dir
        self.powershell_process = None
        
    def __del__(self):
        """Clean up PowerShell process on deletion."""
        if self.powershell_process:
            self.powershell_process.terminate()
            self.powershell_process = None
    
    def _ensure_powershell_session(self):
        """Ensure a persistent PowerShell session exists."""
        if not self.powershell_process or self.powershell_process.poll() is not None:
            # Start a new PowerShell session
            self.powershell_process = subprocess.Popen(
                ['powershell', '-NoProfile', '-NonInteractive'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True,
                cwd=self.project_dir
            )
    
    def set_project_dir(self, directory):
        """
        Set the project directory for command execution.
        
        Args:
            directory (str): The directory path to set
        """
        self.project_dir = directory
        # Only start PowerShell session when actually executing commands
        if self.powershell_process:
            self.powershell_process.terminate()
            self.powershell_process = None

    def is_path_in_project(self, path):
        """
        Check if a path is within the project directory.
        
        Args:
            path (str): The path to check
            
        Returns:
            bool: True if the path is within project directory, False otherwise
        """
        if not self.project_dir:
            return False
            
        try:
            # Block paths with null bytes
            if '\0' in path:
                return False
                
            # Convert paths to absolute, handling relative paths from project directory
            if os.path.isabs(path):
                abs_path = os.path.abspath(path)
            else:
                # For relative paths, join with project directory first
                abs_path = os.path.abspath(os.path.join(self.project_dir, path))
            
            project_path = os.path.abspath(self.project_dir)
            
            # Check if the path is the project directory or a subdirectory of it
            try:
                rel_path = os.path.relpath(abs_path, project_path)
                # Block paths that try to escape using .. or start with ~
                if rel_path.startswith('..') or path.startswith('~'):
                    return False
                return True
            except ValueError:
                # Handle path on different drive
                return False
        except (ValueError, OSError):
            # Handle other OS errors
            return False
    
    def is_safe_command(self, command):
        """
        Check if a command is safe to execute by verifying it only accesses the project directory.
        Allows common Windows commands while ensuring they only operate within project directory.
        
        Args:
            command (str): The command to check
            
        Returns:
            bool: True if the command is safe, False otherwise
        """
        if not self.project_dir:
            return False
            
        # Split command and normalize to lowercase for consistent checking
        cmd_parts = command.lower().split()
        if not cmd_parts:
            return False
        
        # Block dangerous system-wide commands
        dangerous_commands = ['format']
        if cmd_parts[0] in dangerous_commands:
            return False
            
        # Check if the command tries to navigate outside project directory using .. or ~
        if '..' in command or '~' in command:
            return False
            
        # List of safe Windows commands that only need path validation
        safe_commands = {
            'dir': 1,      # dir [path]
            'type': 1,     # type [file]
            'move': 2,     # move [source] [dest]
            'ren': 2,      # ren [oldname] [newname]
            'rename': 2,   # rename [oldname] [newname]
            'del': 1,      # del [file]
            'rm': 1,       # rm [file]
            'rmdir': 1,    # rmdir [directory]
            'rd': 1        # rd [directory]
        }
        
        # If it's a known safe command, verify its paths
        if cmd_parts[0] in safe_commands:
            expected_args = safe_commands[cmd_parts[0]]
            # For commands with no args (like plain 'dir'), always allow within project dir
            if len(cmd_parts) == 1 and cmd_parts[0] == 'dir':
                return True
                
            # Check if we have the right number of arguments
            if len(cmd_parts) < expected_args + 1:
                return False
            
            # Verify all path arguments are within project directory
            for i in range(1, expected_args + 1):
                if i < len(cmd_parts):
                    path = cmd_parts[i].strip('"\'')
                    if not self.is_path_in_project(path):
                        return False
            return True
            
        # For PowerShell commands like Add-Content and Set-Content, check the -Path parameter
        if cmd_parts[0] in ['add-content', 'set-content', 'new-item']:
            path_match = re.search(r'-Path\s+([^\s]+)', command)
            if path_match:
                path = path_match.group(1).strip('"\'')
                return self.is_path_in_project(path)
        
        # Check if any absolute paths in the command are within project directory
        parts = command.split()
        for part in parts:
            if ':' in part:  # Windows absolute path
                # Remove any quotes around the path
                clean_part = part.strip('"\'')
                if not self.is_path_in_project(clean_part):
                    return False
                    
        return True

    def safe_write_file(self, filepath, content):
        """
        Safely write content to a file within the project directory.
        
        Args:
            filepath (str): Path to the file to write
            content (str): Content to write to the file
            
        Returns:
            tuple: (success, error_message)
        """
        if not self.is_path_in_project(filepath):
            return False, "File path is outside project directory"
            
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            
            # Write file in chunks
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write in chunks if content is large
                start = 0
                while start < len(content):
                    chunk = content[start:start + self.CHUNK_SIZE]
                    f.write(chunk)
                    start += self.CHUNK_SIZE
                    
            return True, None
        except Exception as e:
            return False, str(e)

    def safe_read_file(self, filepath):
        """
        Safely read content from a file within the project directory.
        
        Args:
            filepath (str): Path to the file to read
            
        Returns:
            tuple: (content, error_message)
        """
        if not self.is_path_in_project(filepath):
            return None, "File path is outside project directory"
            
        try:
            content = []
            with open(filepath, 'r', encoding='utf-8') as f:
                while True:
                    chunk = f.read(self.CHUNK_SIZE)
                    if not chunk:
                        break
                    content.append(chunk)
            return ''.join(content), None
        except Exception as e:
            return None, str(e)

    def safe_copy_file(self, src, dst):
        """
        Safely copy a file within the project directory.
        
        Args:
            src (str): Source file path
            dst (str): Destination file path
            
        Returns:
            tuple: (success, error_message)
        """
        if not (self.is_path_in_project(src) and self.is_path_in_project(dst)):
            return False, "Source or destination path is outside project directory"
            
        try:
            shutil.copy2(src, dst)
            return True, None
        except Exception as e:
            return False, str(e)
    
    def preprocess_command(self, command):
        """
        Preprocess command to handle special cases like multiline commands.
        Converts multiline commands to single-line format.
        
        Args:
            command (str): The command to preprocess
            
        Returns:
            str: Preprocessed command
        """
        # Special case: Set-Content with triple quotes for Python script
        if command.startswith('Set-Content') and '-Path' in command and '-Value' in command:
            # Extract path
            path_match = re.search(r'-Path\s+([^\s]+)', command)
            if path_match:
                filepath = path_match.group(1).strip('"\'')
                
                # Check if this is a Python script with multiline content
                if filepath.lower().endswith('.py') and ('"""' in command or '@"' in command):
                    # Extract content based on Python script pattern
                    if '"""' in command:
                        try:
                            content_start = command.index('"""') + 3
                            content_end = command.rindex('"""')
                            if content_start < content_end:
                                content = command[content_start:content_end].strip()
                                # Use echo with file redirection instead
                                return f'echo {content} > {filepath}'
                        except Exception:
                            # If we can't extract content, proceed with original command
                            pass
                    elif '@"' in command and '"@' in command:
                        try:
                            content_start = command.index('@"') + 2
                            content_end = command.rindex('"@')
                            if content_start < content_end:  # Fixed variable names
                                content = command[content_start:content_end].strip()
                                # Use echo with file redirection instead
                                return f'echo {content} > {filepath}'
                        except Exception:
                            # If we can't extract content, proceed with original command
                            pass
        
        return command
    
    def handle_set_content(self, command):
        """
        Directly handle Set-Content commands by extracting path and content.
        
        Args:
            command (str): The Set-Content command to handle
            
        Returns:
            tuple: (success, output, error) - success flag, output message, and error message
        """
        try:
            # Extract path
            path_match = re.search(r'-Path\s+([^\s]+)', command)
            if not path_match:
                return False, None, "Invalid Set-Content command format: missing -Path"
                
            filepath = path_match.group(1).strip('"\'')
            
            # Extract content - everything after -Value
            value_parts = command.split('-Value', 1)
            if len(value_parts) != 2:
                return False, None, "Invalid Set-Content command format: missing -Value"
            
            value = value_parts[1].strip()
            content = ""
            
            # Test for different quoting styles
            if '@"' in value and '"@' in value:
                # Here-string
                here_start = value.find('@"') + 2
                here_end = value.rfind('"@')
                if here_start < here_end:
                    content = value[here_start:here_end]
            elif '"""' in value:
                # Triple quotes
                triple_start = value.find('"""') + 3
                triple_end = value.rfind('"""')
                if triple_start < triple_end:
                    content = value[triple_start:triple_end]
            elif value.startswith('"') and value.endswith('"'):
                # Double quotes
                content = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                # Single quotes
                content = value[1:-1]
            else:
                # Plain text
                content = value
            
            # For Python files - handle indentation and do special processing
            if filepath.lower().endswith('.py'):
                # Remove common indentation
                lines = content.split('\n')
                if lines:
                    # Find minimum indentation (ignoring empty lines)
                    min_indent = float('inf')
                    for line in lines:
                        if line.strip():  # Skip empty lines
                            indent = len(line) - len(line.lstrip())
                            min_indent = min(min_indent, indent)
                    
                    # Remove that much indentation from all lines
                    if min_indent < float('inf'):
                        content = '\n'.join(line[min_indent:] if line.strip() else line for line in lines)
                
                # Handle any docstring triple quotes in content
                if '"""' in content:
                    # Make sure we don't strip these
                    content = content.replace('\\"\\"\\"', '"""')
            
            # Write the content to the file
            success, error = self.safe_write_file(filepath, content)
            if success:
                return True, "File written successfully", None
            else:
                return False, None, f"Failed to write file: {error}"
                
        except Exception as e:
            return False, None, f"Error handling Set-Content: {str(e)}"

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

        # Special handling for Set-Content and Add-Content commands
        if command.startswith('Set-Content') or command.startswith('Add-Content'):
            success, output, error = self.handle_content_command(command)
            return output, error, success

        # Direct file write handling for commands with > operator
        if '>' in command:
            write_idx = command.index('>')
            content = command[:write_idx].strip()
            filepath = command[write_idx + 1:].strip()
            
            # Remove surrounding quotes from filepath if present
            if (filepath.startswith('"') and filepath.endswith('"')) or \
               (filepath.startswith("'") and filepath.endswith("'")):
                filepath = filepath[1:-1]
            
            # Handle PowerShell here-string syntax (@'...'@)
            if content.startswith("$") and "@'" in content:
                # Extract the actual content between the here-string markers
                start_marker = content.index("@'") + 2
                end_marker = content.rindex("'@")
                if start_marker < end_marker:
                    content = content[start_marker:end_marker].strip()
                    success, error = self.safe_write_file(filepath, content)
                    return ('File written successfully' if success else None,
                            error if not success else None,
                            success)
            
            # Handle regular echo command
            elif content.lower().startswith('echo '):
                content = content[5:].strip()  # Remove 'echo '
                # Remove surrounding quotes if present
                if (content.startswith('"') and content.endswith('"')) or \
                   (content.startswith("'") and content.endswith("'")):
                    content = content[1:-1]
                success, error = self.safe_write_file(filepath, content)
                return ('File written successfully' if success else None,
                        error if not success else None,
                        success)

        # Execute command in persistent PowerShell session
        self._ensure_powershell_session()
        
        # Add command terminator and output markers for reliable output capture
        marked_command = f"""
echo "===OUTPUT_START===";
{command};
$LASTEXITCODE;
echo "===OUTPUT_END===";
echo "===ERROR_START===";
$Error[0];
echo "===ERROR_END===";
$Error.Clear();
"""
        
        self.powershell_process.stdin.write(marked_command + '\n')
        self.powershell_process.stdin.flush()
        
        # Read output until we see our markers
        output = []
        error = []
        in_output = False
        in_error = False
        
        while True:
            line = self.powershell_process.stdout.readline().rstrip()
            if not line:
                continue
                
            if line == "===OUTPUT_START===":
                in_output = True
                continue
            elif line == "===OUTPUT_END===":
                in_output = False
                continue
            elif line == "===ERROR_START===":
                in_error = True
                continue
            elif line == "===ERROR_END===":
                in_error = False
                break
                
            if in_output:
                output.append(line)
            elif in_error and line != "":
                error.append(line)
        
        stdout = '\n'.join(output[:-1])  # Exclude the exit code
        stderr = '\n'.join(error)
        
        # Check if command was successful (last line of output is exit code)
        try:
            exit_code = int(output[-1])
            is_success = exit_code == 0
        except (IndexError, ValueError):
            is_success = not stderr
        
        return stdout, stderr, True

    def handle_content_command(self, command):
        """
        Handle Set-Content and Add-Content commands by extracting path and content.
        
        Args:
            command (str): The command to handle
            
        Returns:
            tuple: (success, output, error) - success flag, output message, and error message
        """
        try:
            # Extract path
            path_match = re.search(r'-Path\s+([^\s]+)', command)
            if not path_match:
                return False, None, "Invalid command format: missing -Path"
                
            filepath = path_match.group(1).strip('"\'')
            
            # Extract content - everything after -Value
            value_parts = command.split('-Value', 1)
            if len(value_parts) != 2:
                return False, None, "Invalid command format: missing -Value"
            
            value = value_parts[1].strip()
            content = ""
            
            # Test for different quoting styles
            if '@"' in value and '"@' in value:
                # Here-string
                here_start = value.find('@"') + 2
                here_end = value.rfind('"@')
                if here_start < here_end:
                    content = value[here_start:here_end]
            elif '"""' in value:
                # Triple quotes
                triple_start = value.find('"""') + 3
                triple_end = value.rfind('"""')
                if triple_start < triple_end:
                    content = value[triple_start:triple_end]
            elif value.startswith('"') and value.endswith('"'):
                # Double quotes - handle escaped characters
                content = value[1:-1]
                # Convert literal \n to actual newlines
                content = content.encode('utf-8').decode('unicode_escape')
            elif value.startswith("'") and value.endswith("'"):
                # Single quotes
                content = value[1:-1]
                # Convert literal \n to actual newlines
                content = content.encode('utf-8').decode('unicode_escape')
            else:
                # Plain text
                content = value
                # Convert literal \n to actual newlines if they exist
                if '\\n' in content:
                    content = content.encode('utf-8').decode('unicode_escape')
            
            # For Python files - handle indentation and do special processing
            if filepath.lower().endswith('.py'):
                # Remove common indentation
                lines = content.split('\n')
                if lines:
                    # Find minimum indentation (ignoring empty lines)
                    min_indent = float('inf')
                    for line in lines:
                        if line.strip():  # Skip empty lines
                            indent = len(line) - len(line.lstrip())
                            min_indent = min(min_indent, indent)
                    
                    # Remove that much indentation from all lines
                    if min_indent < float('inf'):
                        content = '\n'.join(line[min_indent:] if line.strip() else line for line in lines)
                
                # Preserve docstrings by handling escaped quotes
                content = content.replace('\\"\\"\\"', '"""')
            
            # Write the content to the file
            success, error = self.safe_write_file(filepath, content)
            if success:
                return True, "File written successfully", None
            else:
                return False, None, f"Failed to write file: {error}"
                
        except Exception as e:
            return False, None, f"Error handling content command: {str(e)}"

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