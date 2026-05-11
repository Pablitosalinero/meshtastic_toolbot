import os
import yaml
import time
from platformdirs import user_config_dir, user_data_dir

# Application name for platformdirs
APP_NAME = "meshtastic-toolbot"

class Config:
    def __init__(self, config_path=None):
        # Determine the best path for config and data
        self.config_dir = user_config_dir(APP_NAME)
        self.data_dir = user_data_dir(APP_NAME)
        
        # Ensure directories exist
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        
        if config_path is None:
            self.config_path = os.path.join(self.config_dir, "config.yaml")
        else:
            self.config_path = config_path
            
        self.location = "Unknown Location"
        self.channel = "Test"
        self.port = None
        self.cooldown_seconds = 20
        # Default database path in user data dir
        self.log_file = os.path.join(self.data_dir, "toolbot.db")
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
                # If log_file in yaml is a relative path, put it in data_dir
                log_file_val = data.get("log_file", self.log_file)
                if not os.path.isabs(log_file_val):
                    self.log_file = os.path.join(self.data_dir, log_file_val)
                else:
                    self.log_file = log_file_val
                    
                self.enabled_commands = data.get("enabled_commands", self.enabled_commands)
            except Exception as e:
                print(f"[!] Error loading config file: {e}")

    def save_defaults(self):
        # We store relative log_file name in the yaml for portability
        log_basename = os.path.basename(self.log_file)
        
        default_config = {
            "location": self.location,
            "channel": self.channel,
            "port": self.port,
            "cooldown_seconds": self.cooldown_seconds,
            "log_file": log_basename,
            "enabled_commands": self.enabled_commands
        }
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(default_config, f, default_flow_style=False)
            print(f"[*] Created default configuration at: {self.config_path}")
        except Exception as e:
            print(f"[!] Could not create default config: {e}")
