import json
from src.chat_client import ChatClient
from src.command_executor import CommandExecutor

class Orchestrator:
    def __init__(self, chat_client: ChatClient, command_executor: CommandExecutor):
        self.chat_client = chat_client
        self.command_executor = command_executor
        self.goal = None
        self.plan = []

    def set_goal(self, goal: str):
        self.goal = goal

    def create_plan(self):
        prompt = f"Create a step-by-step plan to achieve the following goal: {self.goal}. The plan should be a list of clear, actionable steps. Return the plan as a JSON list of strings."
        response = self.chat_client.send_message(prompt)
        plan_str = response["message"]
        self.plan = json.loads(plan_str)

    def execute_plan(self):
        for step in self.plan:
            prompt = f"Goal: {self.goal}\nCurrent Step: {step}\n\nGenerate the commands to complete this step. If no commands are needed, return an empty list."
            response = self.chat_client.send_message(prompt)
            commands = response.get("commands", [])
            if commands:
                for command in commands:
                    output = self.command_executor.execute_command(command)
                    print(output)