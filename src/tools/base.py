from abc import ABC, abstractmethod

class Tool(ABC):
    """
    Abstract base class for all tools.
    """
    def __init__(self, name: str, description: str, parameters: list):
        self.name = name
        self.description = description
        self.parameters = parameters

    @abstractmethod
    def execute(self, **kwargs):
        """
        Execute the tool's functionality.
        """
        pass