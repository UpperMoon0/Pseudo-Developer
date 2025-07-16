import os
from collections import deque
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from command_executor import CommandExecutor
from chat_client import ChatClient

class ChatLayout(BoxLayout):
    pass

class ChatApp(App):
    def build(self):
        self.message_history = deque(maxlen=20)
        self.project_dir = None
        self.command_executor = CommandExecutor()
        self.chat_client = ChatClient()
        
        return ChatLayout()

    def save_project_directory(self):
        dir_path = self.root.ids.project_dir_input.text
        if not dir_path:
            self.root.ids.chat_history.text += "[color=ff0000]Error: Please enter a directory path[/color]\n"
            return

        try:
            os.makedirs(dir_path, exist_ok=True)
            self.project_dir = os.path.abspath(dir_path)
            self.command_executor.set_project_dir(self.project_dir)
            self.root.ids.chat_history.text += f"[color=00ff00]Success: Directory saved - {dir_path}[/color]\n"
        except Exception as e:
            self.root.ids.chat_history.text += f"[color=ff0000]Error: Failed to create directory - {str(e)}[/color]\n"

    def send_message(self):
        user_message = self.root.ids.message_input.text
        if not user_message:
            return

        if not self.project_dir:
            self.root.ids.chat_history.text += "[color=ff0000]Please set a project directory first.[/color]\n"
            return

        self.message_history.append(("user", user_message))
        self.update_chat_display()
        
        messages = [{"role": role, "content": content} for role, content in self.message_history]
        
        Clock.schedule_once(lambda dt: self.get_ai_response(messages))
        self.root.ids.message_input.text = ""

    def get_ai_response(self, messages):
        try:
            response_data = self.chat_client.get_response(messages, self.project_dir)
            ai_message = response_data["message"]
            self.message_history.append(("assistant", ai_message))
            self.update_chat_display()

            if 'commands' in response_data and response_data['commands']:
                results = self.command_executor.execute_commands(response_data['commands'])
                self.process_command_results(results)
        except Exception as e:
            self.root.ids.chat_history.text += f"[color=ff0000]Error: {str(e)}[/color]\n"

    def process_command_results(self, results):
        for result in results:
            self.root.ids.chat_history.text += f"[color=00ffff]Command: {result['command']}[/color]\n"
            if result['stdout']:
                self.root.ids.chat_history.text += f"Output: {result['stdout']}\n"
            if result['stderr']:
                self.root.ids.chat_history.text += f"Error: {result['stderr']}\n"

    def update_chat_display(self):
        chat_text = ""
        for role, content in self.message_history:
            if content:
                color = "00ff00" if role == "user" else "ffffff"
                chat_text += f"[color={color}]{role.capitalize()}: {content}[/color]\n"
        self.root.ids.chat_history.text = chat_text

if __name__ == '__main__':
    ChatApp().run()