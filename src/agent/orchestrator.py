import json
from src.chat_client import ChatClient
from src.tool_executor import ToolExecutor

class Orchestrator:
    def __init__(self, chat_client: ChatClient, tool_executor: ToolExecutor):
        self.chat_client = chat_client
        self.tool_executor = tool_executor
        self.goal = None
        self.plan = []

    def set_goal(self, goal: str):
        self.goal = goal

    def create_plan(self):
        prompt = f"Create a step-by-step plan to achieve the following goal: {self.goal}. The plan should be a list of clear, actionable steps. Return the plan as a JSON list of strings."
        messages = [{"role": "user", "parts": [{"text": prompt}]}]
        response = self.chat_client.get_response(messages, ".")
        plan_str = response["message"]
        try:
            self.plan = json.loads(plan_str)
        except json.JSONDecodeError:
            print(f"Failed to decode plan. Response: {plan_str}")
            self.plan = []

    def execute_plan(self):
        for step in self.plan:
            tool_defs = self.tool_executor.get_tool_definitions()
            prompt = f"""
Goal: {self.goal}
Current Step: {step}
Available Tools: {json.dumps(tool_defs, indent=2)}

Based on the current step, which tool should be used?
Return a JSON object with "tool_name" and "arguments".
"""
            messages = [{"role": "user", "parts": [{"text": prompt}]}]
            response = self.chat_client.get_response(messages, ".")
            tool_call_str = response["message"]
            try:
                tool_call = json.loads(tool_call_str)
                tool_name = tool_call["tool_name"]
                arguments = tool_call["arguments"]
                result = self.tool_executor.execute_tool(tool_name, **arguments)
                print(result)
            except (json.JSONDecodeError, KeyError):
                print(f"Failed to process tool call. Response: {tool_call_str}")