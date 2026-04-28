import time
from pubsub import pub
from meshtastic_toolbot.connection import connect
from meshtastic_toolbot.packets import extract_text_message, get_channel_name
from meshtastic_toolbot.commands import COMMAND_REGISTRY

class MeshtasticBot:
    def __init__(self, config, db):
        self.config = config
        self.db = db
        self.interface = None

    def start(self):
        print("Starting Meshtastic Bot Engine...")
        pub.subscribe(self.on_receive, "meshtastic.receive")
        
        self.interface = connect(self.config.port)
        
        print("\n--- YOUR LOCAL CHANNELS ---")
        target_channel_idx = None
        if hasattr(self.interface, 'localNode') and hasattr(self.interface.localNode, 'channels'):
            for idx, ch in enumerate(self.interface.localNode.channels):
                if hasattr(ch, 'settings'):
                    c_name = ch.settings.name
                    c_role = ch.role
                    if c_role != 0:
                        print(f"> Index: {idx} | Role: {c_role} | Saved Name: '{c_name}'")
                        if c_name.lower() == self.config.channel.lower():
                            target_channel_idx = idx
        print("---------------------------\n")

        if target_channel_idx is not None:
            print(f"Sending startup message to channel '{self.config.channel}' (Index {target_channel_idx})...")
            my_name = self.interface.getLongName() or "Unknown"
            startup_msg = f"🟢 {my_name} is online at {self.config.location}!\nSend /status or /ping for network telemetry."
            self.interface.sendText(startup_msg, channelIndex=target_channel_idx)

        print(f"Waiting for commands on channel '{self.config.channel}'...")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Bot shutting down...")
            if self.interface:
                self.interface.close()

    def on_receive(self, packet, interface):
        try:
            msg_data = extract_text_message(packet)
            if not msg_data:
                return
                
            portnum, text, channel_index, from_node, reply_to_id = msg_data
            
            # Ignore our own messages
            my_node_num = interface.myInfo.my_node_num if hasattr(interface, 'myInfo') else None
            if from_node == my_node_num:
                return 
                
            channel_name = get_channel_name(interface, channel_index)
            print(f"[*] Message received -> Channel: '{channel_name}' | Index: {channel_index} | Text: '{text}'")

            # Check if message is in target channel
            if channel_name.lower() != self.config.channel.lower():
                return
                
            # Process commands
            text = text.strip().lower()
            cmd_parts = text.split(maxsplit=1)
            cmd_name = cmd_parts[0]
            cmd_args = cmd_parts[1] if len(cmd_parts) > 1 else ""
            
            if cmd_name in COMMAND_REGISTRY:
                # Target filtering check
                if cmd_args:
                    my_long_name = (interface.getLongName() or "").lower()
                    my_short_name = (interface.getShortName() or "").lower()
                    target = cmd_args.replace("@", "").lower()
                    
                    if target not in my_long_name and target not in my_short_name:
                        print(f"[-] Command ignored: Targeted at '{target}', my name is '{my_long_name}'/'{my_short_name}'.")
                        return

                # Remove slash to check config enabled list
                base_cmd_name = cmd_name.lstrip("/")
                
                if base_cmd_name in self.config.enabled_commands:
                    # Enforce Cooldown
                    if self.db.check_and_update_cooldown(from_node, self.config.cooldown_seconds):
                        handler_class = COMMAND_REGISTRY[cmd_name]
                        handler = handler_class(self.config, self.db, self.interface)
                        handler.handle(packet, channel_index, from_node, reply_to_id, cmd_args)
                    else:
                        print(f"[-] Dropping command from {from_node}: Cooldown active.")
                else:
                    print(f"[-] Command {cmd_name} is disabled in config.")
                    
        except Exception as e:
            print(f"[!] Error processing packet: {e}")
