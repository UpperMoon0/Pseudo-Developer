from abc import ABC, abstractmethod

class Tool(ABC):
    """
    Abstract base class for all tools.
    """
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def execute(self, *args, **kwargs):
        """
        Execute the tool's functionality.
        """
        pass