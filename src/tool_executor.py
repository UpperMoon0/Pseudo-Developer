import inspect
import pkgutil
import importlib
from src.tools.base import Tool
import src.tools

class ToolExecutor:
    def __init__(self):
        self.tools = {}
        self._discover_tools()

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
            return self.tools[tool_name].execute(**kwargs)
        return f"Error: Tool '{tool_name}' not found."