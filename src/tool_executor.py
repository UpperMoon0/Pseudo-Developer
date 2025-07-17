import inspect
import pkgutil
import importlib
import os
from src.tools.base import Tool
import src.tools

class ToolExecutor:
    def __init__(self):
        self.tools = {}
        self.project_dir = None
        self._discover_tools()

    def set_project_dir(self, project_dir: str):
        self.project_dir = project_dir

    def _discover_tools(self):
        for _, modname, _ in pkgutil.walk_packages(src.tools.__path__, src.tools.__name__ + '.'):
            module = importlib.import_module(modname)
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, Tool) and obj is not Tool:
                    tool_instance = obj()
                    self.tools[tool_instance.name] = tool_instance

    def get_tool_definitions(self):
        return [
            {"name": tool.name, "description": tool.description}
            for tool in self.tools.values()
        ]

    def execute_tool(self, tool_name: str, **kwargs):
        if tool_name in self.tools:
            if self.project_dir:
                if 'path' in kwargs and not os.path.isabs(kwargs['path']):
                    kwargs['path'] = os.path.join(self.project_dir, kwargs['path'])
                if tool_name == "execute_shell":
                    kwargs['cwd'] = self.project_dir
            return self.tools[tool_name].execute(**kwargs)
        return f"Error: Tool '{tool_name}' not found."