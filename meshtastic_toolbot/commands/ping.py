from meshtastic_toolbot.commands.base import BaseCommand
from meshtastic_toolbot.packets import get_telemetry_metrics, identify_relay, get_node_name
from meshtastic_toolbot.formatters.visual import get_hops_visual, get_signal_icons

class PingCommand(BaseCommand):
    def handle(self, packet, channel_index, from_node, reply_to_id, text_args):
        print(">>> Command /ping detected! Gathering metrics...")
        
        rssi, snr, hop_start, hop_limit = get_telemetry_metrics(packet)
        visual_hops = get_hops_visual(hop_start, hop_limit)
        icon_rssi, icon_snr = get_signal_icons(rssi, snr)
        
        real_relay_id, relay_name = identify_relay(packet, self.interface, hop_start, hop_limit)
        str_last_node = f"\nRelay: {relay_name}"
        
        sender_name = get_node_name(self.interface, from_node)

        # Assemble final compact and visual message
        reply = f"Ping for: {sender_name}\n"
        reply += f"Location: {self.config.location}\n"
        reply += f"RSSI: {rssi} dBm {icon_rssi}\n"
        reply += f"SNR: {snr} dB {icon_snr}\n"
        reply += f"Hops: {visual_hops}{str_last_node}"

        # Send response with stats linked to the original message
        self.interface.sendText(reply, channelIndex=channel_index, replyId=reply_to_id)
        
        # Log telemetry to DB
        self.db.log_telemetry(from_node, self.config.channel, rssi, snr, hop_start, hop_limit, real_relay_id, "/ping")
