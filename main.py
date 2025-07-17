import os
from src.agent.orchestrator import Orchestrator
from src.chat_client import ChatClient
from src.tool_executor import ToolExecutor

if __name__ == "__main__":
    chat_client = ChatClient()
    tool_executor = ToolExecutor()
    orchestrator = Orchestrator(chat_client, tool_executor)

    goal = input("Please enter your high-level goal: ")
    orchestrator.set_goal(goal)
    orchestrator.create_plan()

    print("Generated Plan:", orchestrator.plan)

    orchestrator.execute_plan()

    print("Goal execution finished.")