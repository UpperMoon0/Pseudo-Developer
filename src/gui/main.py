import os
import logging
import threading
import json
import platformdirs
from collections import deque
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
from kivy.clock import Clock
from src.chat_client import ChatClient
from src.tool_executor import ToolExecutor

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class PseudoDeveloperLayout(BoxLayout):
    pass

class PseudoDeveloperApp(App):
    selected_api_key = StringProperty(None, allownone=True)

    def build(self):
        logging.info("Building PseudoDeveloperApp GUI.")
        self.message_history = deque(maxlen=20)
        self.project_dir = None
        self.chat_client = ChatClient()
        self.command_executor = ToolExecutor()
        self.settings_path = self._get_settings_path()
        
        return PseudoDeveloperLayout()

    def on_start(self):
        logging.info("PseudoDeveloperApp GUI build complete.")
        self.load_api_keys_to_gui()
        self.load_settings()

    def _get_settings_path(self):
        app_dir = platformdirs.user_data_dir("PseudoDeveloper", "NsTut")
        os.makedirs(app_dir, exist_ok=True)
        return os.path.join(app_dir, "settings.json")

    def load_settings(self):
        if os.path.exists(self.settings_path):
            with open(self.settings_path, 'r') as f:
                try:
                    settings = json.load(f)
                    self.project_dir = settings.get("project_dir")
                    if self.project_dir:
                        self.root.ids.project_dir_input.text = self.project_dir
                        self.command_executor.set_project_dir(self.project_dir)
                except json.JSONDecodeError:
                    pass

    def save_settings(self):
        with open(self.settings_path, 'w') as f:
            json.dump({"project_dir": self.project_dir}, f, indent=4)

    def load_api_keys_to_gui(self):
        logging.info("Loading API keys to GUI.")
        keys = self.chat_client.get_api_keys()
        self.root.ids.api_key_list.data = [{'text': key} for key in keys]
        logging.info("Finished loading API keys to GUI.")

    def add_api_key(self):
        new_key = self.root.ids.new_api_key_input.text
        if new_key:
            self.chat_client.add_api_key(new_key)
            self.load_api_keys_to_gui()
            self.root.ids.new_api_key_input.text = ""
            logging.info("Successfully added new API key.")
        else:
            logging.warning("Add API key called with no key.")

    def remove_api_key(self):
        if self.selected_api_key:
            self.chat_client.remove_api_key(self.selected_api_key)
            self.load_api_keys_to_gui()
            logging.info(f"Removed API key: {self.selected_api_key}")
            self.selected_api_key = None
        else:
            logging.warning("Remove API key called with no key selected.")

    def select_api_key(self, key):
        self.selected_api_key = key
        logging.info(f"Selected API key set to: {self.selected_api_key}")
        self.root.ids.api_key_list.refresh_from_data()

    def save_project_directory(self):
        dir_path = self.root.ids.project_dir_input.text
        if not dir_path:
            self.root.ids.chat_history.text += "[color=ff0000]Error: Please enter a directory path[/color]\n"
            return

        try:
            os.makedirs(dir_path, exist_ok=True)
            self.project_dir = os.path.abspath(dir_path)
            self.command_executor.set_project_dir(self.project_dir)
            self.save_settings()
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
        
        messages = [{"role": role, "parts": [{"text": content}]} for role, content in self.message_history]
        
        threading.Thread(target=self.get_ai_response, args=(messages,)).start()
        self.root.ids.message_input.text = ""

    def get_ai_response(self, messages):
        try:
            tool_definitions = self.command_executor.get_tool_definitions()
            response = self.chat_client.get_response(messages, tool_definitions)
            
            if isinstance(response, dict) and "message" in response:
                error_message = response["message"]
                logging.error(error_message)
                Clock.schedule_once(lambda dt: self.update_ui_with_error(error_message))
                return

            ai_message = ""
            commands = []
            
            if response and hasattr(response, 'candidates') and response.candidates:
                for part in response.candidates[0].content.parts:
                    if part.text:
                        ai_message += part.text
                    if part.function_call:
                        command = {
                            "command": part.function_call.name,
                            "params": dict(part.function_call.args)
                        }
                        commands.append(command)

            Clock.schedule_once(lambda dt: self.update_ui_with_ai_message(ai_message))

            if commands:
                self.execute_commands(commands)
        except Exception as e:
            error_message = f"Error: {str(e)}"
            logging.error(error_message)
            Clock.schedule_once(lambda dt: self.update_ui_with_error(error_message))

    def execute_commands(self, commands):
        for command_info in commands:
            tool_name = command_info.get("command")
            params = command_info.get("params", {})
            
            if tool_name:
                Clock.schedule_once(lambda dt, tn=tool_name, p=params: self.update_ui_with_command_start(tn, p))
                try:
                    result = self.command_executor.execute_tool(tool_name, **params)
                    Clock.schedule_once(lambda dt, r=result: self.update_ui_with_command_result(r))
                except Exception as e:
                    error_message = f"Error executing command {tool_name}: {str(e)}"
                    logging.error(error_message)
                    Clock.schedule_once(lambda dt, em=error_message: self.update_ui_with_error(em))

    def update_ui_with_ai_message(self, ai_message):
        if ai_message:
            self.message_history.append(("assistant", ai_message))
            self.update_chat_display()

    def update_ui_with_command_start(self, tool_name, params):
        self.root.ids.chat_history.text += f"[color=ffff00]Executing command: {tool_name} with params: {params}[/color]\n"

    def update_ui_with_command_result(self, result):
        if isinstance(result, dict):
            formatted_result = "\n"
            for key, value in result.items():
                if value:
                    formatted_result += f"  {key.capitalize()}:\n{value}\n"
            if formatted_result == "\n":
                formatted_result = "Command executed with no output."
        else:
            formatted_result = result
        self.root.ids.chat_history.text += f"[color=00ffff]Command result: {formatted_result}[/color]\n"

    def update_ui_with_error(self, error_message):
        self.root.ids.chat_history.text += f"[color=ff0000]{error_message}[/color]\n"

    def update_chat_display(self):
        chat_text = ""
        for role, content in self.message_history:
            if content:
                color = "00ff00" if role == "user" else "ffffff"
                chat_text += f"[color={color}]{role.capitalize()}: {content}[/color]\n"
        self.root.ids.chat_history.text = chat_text

if __name__ == '__main__':
    PseudoDeveloperApp().run()