import sys
import time
import argparse
from pubsub import pub
import meshtastic
import meshtastic.serial_interface
import serial.tools.list_ports

# --- BOT CONFIGURATION ---
# These will be set via argparse
BOT_LOCATION = "Unknown Location"
TARGET_CHANNEL = "test"
TARGET_PORT = None

def on_receive(packet, interface):
    try:
        # Check if there is decoded data in the packet
        if 'decoded' not in packet:
            return
            
        decoded = packet['decoded']
        portnum = decoded.get('portnum')
        
        # Filter only text messages (portnum 1 or 'TEXT_MESSAGE_APP')
        if portnum == 'TEXT_MESSAGE_APP' or portnum == 1:
            text = decoded.get('text', '')
            channel_index = packet.get('channel', 0)
            
            # Ignore our own messages to prevent loops
            my_node_num = interface.myInfo.my_node_num if hasattr(interface, 'myInfo') else None
            if packet.get('from') == my_node_num:
                return 
            
            # Get the channel name from its index
            channel_name = ""
            if hasattr(interface, 'localNode') and hasattr(interface.localNode, 'channels'):
                if 0 <= channel_index < len(interface.localNode.channels):
                    channel_obj = interface.localNode.channels[channel_index]
                    if hasattr(channel_obj, 'settings') and hasattr(channel_obj.settings, 'name'):
                        channel_name = channel_obj.settings.name

            print(f"[*] Message received -> Channel: '{channel_name}' | Index: {channel_index} | Text: '{text}'")

            # Process the command only if the channel matches our target channel
            if channel_name.lower() == TARGET_CHANNEL.lower() and text.strip().lower() == "/ping":
                print(f">>> Command /ping detected in channel '{channel_name}'! Gathering metrics...")
                
                rssi = packet.get('rxRssi', 'N/A')
                snr = packet.get('rxSnr', 'N/A')
                hop_start = packet.get('hopStart', 'N/A')
                hop_limit = packet.get('hopLimit', 'N/A')
                
                # Visually calculate the number of hops in route
                visual_hops = "N/A"
                if isinstance(hop_start, int) and isinstance(hop_limit, int):
                    hops_taken = max(0, hop_start - hop_limit)
                    visual_hops = ("🟢" * hops_taken) + ("⚪" * hop_limit) + f" ({hops_taken}/{hop_start})"
                
                # Signal quality (RSSI) and Noise (SNR) icons
                icon_rssi = "❔"
                if isinstance(rssi, (int, float)):
                    if rssi >= -70: icon_rssi = "🟢"
                    elif rssi >= -95: icon_rssi = "🟡"
                    else: icon_rssi = "🔴"
                    
                icon_snr = "❔"
                if isinstance(snr, (int, float)):
                    if snr >= 0: icon_snr = "🟢"
                    elif snr >= -10: icon_snr = "🟡"
                    else: icon_snr = "🔴"
                
                # Identify the physical antenna that relayed the packet to our receiver
                relay_byte = packet.get('relayNode')
                real_relay_id = None
                
                # If hops taken is 0, it came direct and the immediate relay is the original sender (from)
                if isinstance(hop_start, int) and isinstance(hop_limit, int) and hop_start == hop_limit:
                    real_relay_id = packet.get('from')
                elif relay_byte is not None and hasattr(interface, 'nodes'):
                    # If routed, Meshtastic trims Relay ID to 1 byte (0-255). We must find a match in the DB
                    for _, n in interface.nodes.items():
                        node_num = n.get('num')
                        if node_num and (node_num & 0xFF) == relay_byte:
                            real_relay_id = node_num
                            break
                            
                if not real_relay_id:
                    real_relay_id = packet.get('from')

                relay_name = "Unknown"
                if real_relay_id and hasattr(interface, 'nodes'):
                    # Search local contacts book using the full expanded ID
                    for _, n in interface.nodes.items():
                        if n.get('num') == real_relay_id:
                            user_data = n.get('user', {})
                            relay_name = user_data.get('longName') or user_data.get('shortName') or f"!{real_relay_id:08x}"
                            break
                            
                if relay_name == "Unknown" and real_relay_id:
                    relay_name = f"!{real_relay_id:08x}" # Fully formatted 32-bit Hex

                str_last_node = f"\nRelay: {relay_name}"

                # Assemble final compact and visual message
                reply = f"Node: {BOT_LOCATION}\n"
                reply += f"RSSI: {rssi} dBm {icon_rssi}\n"
                reply += f"SNR: {snr} dB {icon_snr}\n"
                reply += f"Hops: {visual_hops}{str_last_node}"

                # Send response with stats linked to the original message
                reply_to_id = packet.get('id')
                interface.sendText(reply, channelIndex=channel_index, replyId=reply_to_id)
                
    except Exception as e:
        print(f"[!] Error processing packet: {e}")

def main():
    global BOT_LOCATION, TARGET_CHANNEL, TARGET_PORT

    parser = argparse.ArgumentParser(description="Meshtastic Telemetry Bot")
    parser.add_argument("--location", type=str, default="Unknown Location", 
                        help="Text location of the bot to include in ping responses")
    parser.add_argument("--channel", type=str, default="test", 
                        help="The channel name where the bot will listen for commands")
    parser.add_argument("--port", type=str, default=None, 
                        help="Serial COM port (e.g., COM3). If not provided, it will auto-detect.")
    
    args = parser.parse_args()
    
    BOT_LOCATION = args.location
    TARGET_CHANNEL = args.channel
    TARGET_PORT = args.port

    print(f"Starting Meshtastic Bot...")
    print(f"Location Configured: {BOT_LOCATION}")
    print(f"Target Channel: {TARGET_CHANNEL}")
    pub.subscribe(on_receive, "meshtastic.receive")
    
    device_port = TARGET_PORT
    if not device_port:
        print("Searching for Serial ports...")
        ports = serial.tools.list_ports.comports()
        for p in ports:
            if 'COM' in p.device:
                device_port = p.device
                break
                
    if not device_port:
        print("No serial port found. Check USB connection.")
        sys.exit(1)
        
    print(f"Port detected: {device_port}. Connecting...")
    interface = None
    while True:
        try:
            # Ensure the previous port is released if the previous loop failed
            if interface and hasattr(interface, 'close'):
                try:
                    interface.close()
                except:
                    pass
                time.sleep(1)

            # Manual connection to control pins on Windows
            interface = meshtastic.serial_interface.SerialInterface(devPath=device_port, connectNow=False)
            
            # Release reset pins (very useful for ESP32 chips on Windows)
            if hasattr(interface, 'stream'):
                interface.stream.setDTR(False)
                interface.stream.setRTS(False)
            
            # Wait for board to stabilize
            print("Starting connection (waiting 4 seconds in case the board restarted)...")
            time.sleep(4)
            
            print("Launching handshake protocol with the device...")
            interface.connect()
            
            print("=== CONNECTED ===")
            print(f"The bot is listening on port {device_port}.")
            
            # --- DEBUG: Show configured channels ---
            print("\n--- YOUR LOCAL CHANNELS ---")
            target_channel_idx = None
            if hasattr(interface, 'localNode') and hasattr(interface.localNode, 'channels'):
                for idx, ch in enumerate(interface.localNode.channels):
                    if hasattr(ch, 'settings'):
                        c_name = ch.settings.name
                        c_role = ch.role
                        # Ignore disabled channels (role 0 = DISABLED)
                        if c_role != 0:
                            print(f"> Index: {idx} | Role: {c_role} | Saved Name: '{c_name}'")
                            if c_name.lower() == TARGET_CHANNEL.lower():
                                target_channel_idx = idx
            print("---------------------------\n")

            if target_channel_idx is not None:
                print(f"Sending startup message to channel '{TARGET_CHANNEL}' (Index {target_channel_idx})...")
                my_name = interface.getLongName() or "Unknown"
                startup_msg = f"Telemetry node {my_name} started."
                interface.sendText(startup_msg, channelIndex=target_channel_idx)

            print(f"Waiting for '/ping' commands on channel '{TARGET_CHANNEL}'...")
            
            while True:
                time.sleep(1)
                
        except PermissionError:
            print(f"Port {device_port} is blocked. Close other apps and retry.")
            time.sleep(5)
        except Exception as e:
            print(f"Communication failure: {e} | Retrying in 6s...")
            time.sleep(6)

if __name__ == "__main__":
    main()
