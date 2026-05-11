import traceback
from meshtastic_toolbot.commands.base import BaseCommand
from meshtastic_toolbot.packets import get_telemetry_metrics, identify_relay, get_node_name
from meshtastic_toolbot.formatters.visual import get_hops_visual, get_signal_icons

class PingCommand(BaseCommand):
    def handle(self, packet, channel_index, from_node, reply_to_id, text_args):
        try:
            print(">>> Command /ping detected! Gathering metrics...")
            
            # Robust unpacking to avoid "too many values" error
            metrics = get_telemetry_metrics(packet)
            rssi = metrics[0] if len(metrics) > 0 else "N/A"
            snr = metrics[1] if len(metrics) > 1 else "N/A"
            hop_start = metrics[2] if len(metrics) > 2 else "N/A"
            hop_limit = metrics[3] if len(metrics) > 3 else "N/A"
            
            print(f"DEBUG: Metrics gathered: RSSI={rssi}, SNR={snr}")

            visual_hops = get_hops_visual(hop_start, hop_limit)
            icon_rssi, icon_snr = get_signal_icons(rssi, snr)
            
            # Get relay info (returns hex, names_list, best_id)
            relay_data = identify_relay(packet, self.interface, hop_start, hop_limit)
            relay_hex, relay_names, real_relay_id = relay_data[0], relay_data[1], relay_data[2]
            
            print(f"DEBUG: Relay identified: {relay_hex} with {len(relay_names)} candidates")

            str_relay = f"\nRelay: {relay_hex}"
            for name in relay_names:
                str_relay += f"\n - {name}"
            
            sender_name = get_node_name(self.interface, from_node)

            # Assemble final compact and visual message
            reply = f"Ping for: {sender_name}\n"
            reply += f"Location: {self.config.location}\n"
            reply += f"RSSI: {rssi} dBm {icon_rssi}\n"
            reply += f"SNR: {snr} dB {icon_snr}\n"
            reply += f"Hops: {visual_hops}{str_relay}"

            # Send response with stats linked to the original message
            print(f"DEBUG: Sending reply to channel {channel_index}...")
            self.interface.sendText(reply, channelIndex=channel_index, replyId=reply_to_id)
            
            # Log telemetry to DB
            print(f"DEBUG: Logging to DB...")
            self.db.log_telemetry(from_node, self.config.channel, rssi, snr, hop_start, hop_limit, real_relay_id, "/ping")
            print(">>> Command /ping finished successfully.")
            
        except Exception as e:
            print(f"!!! CRITICAL ERROR in PingCommand: {e}")
            traceback.print_exc()
