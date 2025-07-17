import os
from src.agent.orchestrator import Orchestrator
from src.chat_client import ChatClient
from src.command_executor import CommandExecutor

if __name__ == "__main__":
    PROJECT_DIRECTORY = os.path.join(os.getcwd(), "workspace")
    os.makedirs(PROJECT_DIRECTORY, exist_ok=True)

    chat_client = ChatClient()
    command_executor = CommandExecutor(PROJECT_DIRECTORY)
    orchestrator = Orchestrator(chat_client, command_executor)

    goal = input("Please enter your high-level goal: ")
    orchestrator.set_goal(goal)
    orchestrator.create_plan()

    print("Generated Plan:", orchestrator.plan)

    orchestrator.execute_plan()

    print("Goal execution finished.")