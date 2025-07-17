import subprocess
from src.tools.base import Tool

class ExecuteShellCommandTool(Tool):
    """
    A tool to execute shell commands.
    """
    def __init__(self):
        super().__init__(
            name="execute_shell",
            description="Executes a shell command on the user's operating system."
        )

    def execute(self, command: str) -> dict:
        """
        Executes the given shell command.
        """
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr
        }