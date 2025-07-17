import os
from collections import deque
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
from kivy.clock import Clock
from src.chat_client import ChatClient

class ChatLayout(BoxLayout):
    pass

class ChatApp(App):
    selected_api_key = StringProperty(None, allownone=True)

    def build(self):
        self.message_history = deque(maxlen=20)
        self.project_dir = None
        self.chat_client = ChatClient()
        
        layout = ChatLayout()
        Clock.schedule_once(self.after_build)
        return layout

    def after_build(self, dt):
        self.load_api_keys_to_gui()

    def load_api_keys_to_gui(self):
        keys = self.chat_client.get_api_keys()
        self.root.ids.api_key_list.data = [{'text': key} for key in keys]

    def add_api_key(self):
        new_key = self.root.ids.new_api_key_input.text
        if new_key:
            self.chat_client.add_api_key(new_key)
            self.load_api_keys_to_gui()
            self.root.ids.new_api_key_input.text = ""

    def remove_api_key(self):
        if self.selected_api_key:
            self.chat_client.remove_api_key(self.selected_api_key)
            self.load_api_keys_to_gui()
            self.selected_api_key = None

    def select_api_key(self, key):
        self.selected_api_key = key

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
        
        messages = [{"role": "user", "parts": [{"text": content}]} for role, content in self.message_history if role == "user"]
        
        Clock.schedule_once(lambda dt: self.get_ai_response(messages))
        self.root.ids.message_input.text = ""

    def get_ai_response(self, messages):
        try:
            response_data = self.chat_client.get_response(messages, self.project_dir)
            ai_message = response_data["message"]
            self.message_history.append(("assistant", ai_message))
            self.update_chat_display()
        except Exception as e:
            self.root.ids.chat_history.text += f"[color=ff0000]Error: {str(e)}[/color]\n"

    def update_chat_display(self):
        chat_text = ""
        for role, content in self.message_history:
            if content:
                color = "00ff00" if role == "user" else "ffffff"
                chat_text += f"[color={color}]{role.capitalize()}: {content}[/color]\n"
        self.root.ids.chat_history.text = chat_text

if __name__ == '__main__':
    ChatApp().run()