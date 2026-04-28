import os
import yaml
import time

DEFAULT_CONFIG_FILE = "config.yaml"

class Config:
    def __init__(self, config_path=DEFAULT_CONFIG_FILE):
        self.config_path = config_path
        self.location = "Unknown Location"
        self.channel = "Test"
        self.port = None
        self.cooldown_seconds = 20
        self.log_file = "toolbot.db"
        self.enabled_commands = ["ping", "status"]
        self.start_time = time.time()
        
        self.load()

    def load(self):
        if not os.path.exists(self.config_path):
            self.save_defaults()
            
        with open(self.config_path, "r", encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f) or {}
                self.location = data.get("location", self.location)
                self.channel = data.get("channel", self.channel)
                self.port = data.get("port", self.port)
                self.cooldown_seconds = data.get("cooldown_seconds", self.cooldown_seconds)
                self.log_file = data.get("log_file", self.log_file)
                self.enabled_commands = data.get("enabled_commands", self.enabled_commands)
            except Exception as e:
                print(f"[!] Error loading config file: {e}")

    def save_defaults(self):
        default_config = {
            "location": self.location,
            "channel": self.channel,
            "port": self.port,
            "cooldown_seconds": self.cooldown_seconds,
            "log_file": self.log_file,
            "enabled_commands": self.enabled_commands
        }
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(default_config, f, default_flow_style=False)
        except Exception as e:
            print(f"[!] Could not create default config: {e}")
