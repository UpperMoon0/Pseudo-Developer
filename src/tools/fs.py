import os
from src.tools.base import Tool

class WriteFileTool(Tool):
    """
    A tool to write content to a specified file.
    """
    def __init__(self):
        super().__init__(
            name="write_file",
            description="Writes content to a specified file, creating the file and any necessary directories if they don't exist."
        )

    def execute(self, path: str, content: str):
        """
        Executes the write file tool.

        Args:
            path: The path to the file.
            content: The content to write to the file.
        
        Returns:
            A message indicating the result of the operation.
        """
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                f.write(content)
            return f"File '{path}' written successfully."
        except Exception as e:
            return f"Error writing to file: {e}"

class EditFileTool(Tool):
    """
    A tool to edit a file by replacing a block of text.
    """
    def __init__(self):
        super().__init__(
            name="edit_file",
            description="Replaces a block of text in a specified file."
        )

    def execute(self, path: str, search_block: str, replace_block: str):
        """
        Executes the edit file tool.

        Args:
            path: The path to the file.
            search_block: The block of text to search for.
            replace_block: The block of text to replace the search_block with.
        
        Returns:
            A message indicating the result of the operation.
        """
        try:
            with open(path, 'r') as f:
                content = f.read()
            
            if search_block not in content:
                return f"Error: Search block not found in file '{path}'."

            new_content = content.replace(search_block, replace_block, 1)
            
            with open(path, 'w') as f:
                f.write(new_content)
            
            return f"File '{path}' edited successfully."
        except FileNotFoundError:
            return f"Error: File not found at '{path}'."
        except Exception as e:
            return f"Error editing file: {e}"