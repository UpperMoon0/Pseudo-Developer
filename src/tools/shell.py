import subprocess
from src.tools.base import Tool

class ExecuteShellCommandTool(Tool):
    """
    A tool to execute shell commands.
    """
    def __init__(self):
        super().__init__(
            name="execute_shell",
            description="Executes a shell command on the user's operating system.",
            parameters=[
                {"name": "command", "type": "string", "description": "The shell command to execute.", "required": True},
                {"name": "cwd", "type": "string", "description": "The working directory to execute the command in. Defaults to the project directory."}
            ]
        )

    def execute(self, **kwargs) -> dict:
        """
        Executes the given shell command.
        """
        command = kwargs.get("command")
        cwd = kwargs.get("cwd")
        if not command:
            return {"stdout": "", "stderr": "Error: 'command' parameter is required."}
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=cwd)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr
        }