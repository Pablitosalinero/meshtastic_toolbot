import time
from meshtastic_toolbot.commands.base import BaseCommand
from meshtastic_toolbot import __version__

class StatusCommand(BaseCommand):
    def handle(self, packet, channel_index, from_node, reply_to_id, text_args):
        print(">>> Command /status detected! Sending status...")
        
        # Calculate uptime
        uptime_seconds = int(time.time() - self.config.start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            uptime_str = f"{hours}h {minutes}m"
        elif minutes > 0:
            uptime_str = f"{minutes}m {seconds}s"
        else:
            uptime_str = f"{seconds}s"

        reply = f"🟢 Bot Online\n"
        reply += f"Version: {__version__}\n"
        reply += f"Uptime: {uptime_str}\n"
        reply += f"Location: {self.config.location}"

        self.interface.sendText(reply, channelIndex=channel_index, replyId=reply_to_id)
