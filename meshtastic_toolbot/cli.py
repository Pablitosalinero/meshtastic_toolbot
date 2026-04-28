import argparse
import sys
from meshtastic_toolbot.config import Config
from meshtastic_toolbot.database import Database
from meshtastic_toolbot.bot import MeshtasticBot

def main():
    parser = argparse.ArgumentParser(description="Meshtastic Telemetry Bot")
    parser.add_argument("--location", type=str, default=None, 
                        help="Text location of the bot")
    parser.add_argument("--channel", type=str, default=None, 
                        help="The channel name to listen on")
    parser.add_argument("--port", type=str, default=None, 
                        help="Serial COM port (e.g., COM3). Auto-detects if omitted.")
    parser.add_argument("--cooldown", type=int, default=None,
                        help="Cooldown in seconds per node to prevent spam")
    
    args = parser.parse_args()
    
    # Load config from file, then override with CLI args if provided
    config = Config()
    if args.location is not None:
        config.location = args.location
    if args.channel is not None:
        config.channel = args.channel
    if args.port is not None:
        config.port = args.port
    if args.cooldown is not None:
        config.cooldown_seconds = args.cooldown

    # Init database
    db = Database(config.log_file)
    
    # Start bot
    bot = MeshtasticBot(config, db)
    bot.start()

if __name__ == "__main__":
    main()
