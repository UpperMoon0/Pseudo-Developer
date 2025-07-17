import os
from src.tools.base import Tool

class WriteFileTool(Tool):
    """
    A tool to write content to a specified file.
    """
    def __init__(self):
        super().__init__(
            name="write_file",
            description="Writes content to a specified file, creating the file and any necessary directories if they don't exist.",
            parameters=[
                {"name": "path", "type": "string", "description": "The path to the file.", "required": True},
                {"name": "content", "type": "string", "description": "The content to write to the file.", "required": True}
            ]
        )

    def execute(self, **kwargs):
        """
        Executes the write file tool.
        """
        path = kwargs.get("path")
        content = kwargs.get("content")
        if not path or content is None:
            return "Error: 'path' and 'content' parameters are required."
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
            description="Replaces a block of text in a specified file.",
            parameters=[
                {"name": "path", "type": "string", "description": "The path to the file.", "required": True},
                {"name": "search_block", "type": "string", "description": "The block of text to search for.", "required": True},
                {"name": "replace_block", "type": "string", "description": "The block of text to replace the search_block with.", "required": True}
            ]
        )

    def execute(self, **kwargs):
        """
        Executes the edit file tool.
        """
        path = kwargs.get("path")
        search_block = kwargs.get("search_block")
        replace_block = kwargs.get("replace_block")

        if not path or search_block is None or replace_block is None:
            return "Error: 'path', 'search_block', and 'replace_block' parameters are required."

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